# aggregate_millet_data.py
# Aggregates sentiment and aspect data to create a summary table for each millet type.

import pandas as pd
import os
import ast # To safely evaluate list-like strings from keywords column
from collections import Counter

# --- Define File Names (in the current directory) ---
SENTIMENT_DATA_CSV = 'millet_review_sentiments_groq.csv'
PROCESSED_DATA_CSV = 'final_processed_dataset.csv' # Needed for original ratings
OUTPUT_CSV = 'millet_summary.csv'

def calculate_keyword_freq(series):
    """ Safely evaluates string representations of lists and counts keyword frequencies. """
    all_keywords = []
    for item in series.dropna():
        try:
            # Safely evaluate the string representation of the list
            keywords = ast.literal_eval(item)
            if isinstance(keywords, list):
                all_keywords.extend([kw.lower().strip() for kw in keywords if isinstance(kw, str)])
        except (ValueError, SyntaxError):
            # Handle cases where the string is not a valid list representation
            # print(f"Warning: Could not parse keywords: {item}")
            pass
    return Counter(all_keywords)

def get_top_keywords(counter, top_n=5):
    """ Returns the top N keywords from a Counter object as a list of strings. """
    return [item[0] for item in counter.most_common(top_n)]


def aggregate_data(sentiment_path, processed_path):
    """Loads sentiment data, joins with processed data, and aggregates by millet type."""
    print(f"Loading sentiment data from: {sentiment_path}")
    if not os.path.exists(sentiment_path):
        print(f"Error: Sentiment file not found: {sentiment_path}")
        return None
    try:
        sentiment_df = pd.read_csv(sentiment_path)
        print(f"Loaded {len(sentiment_df)} sentiment records.")
    except Exception as e:
        print(f"Error loading sentiment CSV: {e}")
        return None

    print(f"Loading processed data (for ratings) from: {processed_path}")
    if not os.path.exists(processed_path):
        print(f"Error: Processed data file not found: {processed_path}")
        return None
    try:
        processed_df = pd.read_csv(processed_path)[['review_id', 'rating', 'millet_type']] # Load only needed columns
        print(f"Loaded {len(processed_df)} processed records.")
    except Exception as e:
        print(f"Error loading processed data CSV: {e}")
        return None

    # --- Merge sentiment data with original ratings and millet type ---
    print("Merging sentiment data with processed data...")
    # Validate columns before merging
    if 'review_id' not in sentiment_df.columns or 'review_id' not in processed_df.columns:
        print("Error: 'review_id' column missing in one of the input files. Cannot merge.")
        return None
    if 'millet_type' not in processed_df.columns:
         print("Error: 'millet_type' column missing in processed_df. Cannot aggregate.")
         return None

    merged_df = pd.merge(sentiment_df, processed_df, on='review_id', how='left')
    print(f"Merged dataframe shape: {merged_df.shape}")

    # Check for merge issues (e.g., missing millet_type after merge)
    if merged_df['millet_type'].isnull().any():
        print("Warning: Some reviews could not be matched back to a millet type.")
        merged_df.dropna(subset=['millet_type'], inplace=True) # Drop rows where millet type is missing

    print(f"Aggregating data by millet_type...")

    # Define aggregation functions
    aggregations = {
        'review_id': 'count', # Renamed later to num_reviews
        'rating': 'mean',     # Original star rating average
        'sentiment_score': 'mean', # LLM sentiment score average
        'taste_score': lambda x: x.mean(skipna=True), # Average taste score, ignoring nulls
        'texture_mentioned': lambda x: (x == True).mean(), # Pct where texture mentioned
        'health_benefit_mentioned': lambda x: (x == True).mean(), # Pct health mentioned
        'price_mentioned': lambda x: (x == True).mean(), # Pct price mentioned
        'sentiment_label': lambda x: x.value_counts(normalize=True), # For calculating percentages
        'extracted_keywords': calculate_keyword_freq # Custom aggregation for keywords
    }

    # Group by millet type and aggregate
    summary_df = merged_df.groupby('millet_type').agg(aggregations).reset_index()

    print("Post-processing aggregated data...")

    # Rename count column
    summary_df.rename(columns={'review_id': 'num_reviews',
                               'rating': 'avg_rating'}, inplace=True)

    # Calculate sentiment percentages
    def get_sentiment_pct(sentiment_counts, label):
        if isinstance(sentiment_counts, pd.Series):
            return sentiment_counts.get(label, 0) * 100
        return 0

    summary_df['positive_pct'] = summary_df['sentiment_label'].apply(lambda x: get_sentiment_pct(x, 'positive'))
    summary_df['neutral_pct'] = summary_df['sentiment_label'].apply(lambda x: get_sentiment_pct(x, 'neutral'))
    summary_df['negative_pct'] = summary_df['sentiment_label'].apply(lambda x: get_sentiment_pct(x, 'negative'))

    # Get top keywords
    summary_df['top_keywords'] = summary_df['extracted_keywords'].apply(lambda x: get_top_keywords(x, top_n=10))

    # Drop intermediate columns
    summary_df.drop(columns=['sentiment_label', 'extracted_keywords'], inplace=True)

    # Round numeric columns for readability
    numeric_cols = summary_df.select_dtypes(include='number').columns
    summary_df[numeric_cols] = summary_df[numeric_cols].round(3)

    print("Aggregation complete.")
    return summary_df


def save_summary_data(df, csv_path):
    """Saves the summary DataFrame to the current directory."""
    output_abs_path = os.path.abspath(csv_path)
    print(f"Attempting to save summary data to: {output_abs_path}")
    try:
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"Successfully saved {len(df)} rows to {output_abs_path}")
    except Exception as e:
        print(f"Error saving summary CSV to {output_abs_path}: {e}")

if __name__ == "__main__":
    print("--- Starting Millet Data Aggregation Script ---")

    current_dir = os.getcwd()
    sentiment_file_path = os.path.join(current_dir, SENTIMENT_DATA_CSV)
    processed_file_path = os.path.join(current_dir, PROCESSED_DATA_CSV)
    output_file_path = os.path.join(current_dir, OUTPUT_CSV)

    millet_summary = aggregate_data(sentiment_file_path, processed_file_path)

    if millet_summary is not None and not millet_summary.empty:
        save_summary_data(millet_summary, output_file_path)
        print("\n--- Aggregation Script Completed ---")
        print(f"Output file: {output_file_path}")
        print("\nGenerated Millet Summary:")
        # Display settings to show more columns if needed
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(millet_summary)
    else:
        print("\n--- Aggregation Script Failed ---")
        print("No output file generated. Please check for errors above.")