# clean_data.py
# This script assumes the input CSV is in the SAME folder as this script.
# The output CSV will also be saved in this SAME folder.

import pandas as pd
import os
import re
import uuid
from datetime import datetime
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
# import spacy # Optional alternative

# --- NLTK Data Download (Run these lines once in a Python console if needed) ---
# try:
#     nltk.data.find('corpora/wordnet')
# except nltk.downloader.DownloadError:
#     print("Downloading NLTK wordnet data...")
#     nltk.download('wordnet')
# try:
#     nltk.data.find('corpora/stopwords')
# except nltk.downloader.DownloadError:
#     print("Downloading NLTK stopwords data...")
#     nltk.download('stopwords')
# try:
#      nltk.data.find('corpora/omw-1.4')
# except nltk.downloader.DownloadError:
#      print("Downloading NLTK omw-1.4 data...")
#      nltk.download('omw-1.4')
# print("NLTK data checks complete.")
# --------------------------------------------------------------------------

# --- Define file names (will be used in the current directory) ---
INPUT_CSV = 'dataset_with_lexicon_sentiment.csv'
OUTPUT_CSV = 'final_processed_dataset.csv'

# Initialize lemmatizer and stopwords
lemmatizer = WordNetLemmatizer()
try:
    stop_words = set(stopwords.words('english'))
    # Add common words unlikely to carry specific sentiment if needed
    # stop_words.update(['flipkart', 'amazon', 'bigbasket', 'product', 'item', 'good', 'great', 'nice'])
except LookupError:
    print("NLTK stopwords not found. Please run the NLTK downloads (see comments in code).")
    stop_words = set() # Use an empty set if download fails

def clean_text(text):
    """Applies text cleaning steps to a single review."""
    if pd.isna(text):
        return ""
    text = str(text).lower() # Lowercase
    text = re.sub(r'<.*?>', '', text) # Remove HTML tags
    text = re.sub(r'http\S+|www\S+', '', text) # Remove URLs
    text = re.sub(r'[^a-z\s]', '', text) # Remove non-alphabetic characters (keeps spaces)
    text = re.sub(r'\s+', ' ', text).strip() # Remove extra whitespace

    # Tokenize, remove stopwords, lemmatize
    words = text.split()
    cleaned_words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words and len(word) > 1] # Remove single letters too

    return ' '.join(cleaned_words)

def preprocess_data(input_path):
    """Loads, cleans, and preprocesses the dataset."""
    print(f"Attempting to load data from: {os.path.abspath(input_path)}")
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {os.path.abspath(input_path)}")
        print(f"Please make sure '{INPUT_CSV}' is in the same folder as this script.")
        return None

    try:
        # Specify encoding just in case
        df = pd.read_csv(input_path, encoding='utf-8')
        print(f"Successfully loaded {input_path}")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

    print(f"Initial dataset shape: {df.shape}")
    print(f"Initial columns: {df.columns.tolist()}")

    # --- Standardize expected column names ---
    df.rename(columns={
        'review': 'review_text' # Renaming for consistency with the plan
        # Add other renames here if necessary based on your actual file
    }, inplace=True)

    required_cols = ['rating', 'review_text', 'millet_type', 'platform']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Required columns are missing from the input CSV: {', '.join(missing_cols)}")
        return None

    # 1. Handle missing values in essential columns
    initial_rows = len(df)
    df.dropna(subset=['review_text', 'rating'], inplace=True)
    rows_dropped_na = initial_rows - len(df)
    if rows_dropped_na > 0:
        print(f"Dropped {rows_dropped_na} rows with missing 'review_text' or 'rating'.")
    print(f"Shape after dropping nulls: {df.shape}")

    # 2. Normalize rating
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0).astype(int)
    # Keep only valid ratings (1-5)
    initial_rows = len(df)
    df = df[df['rating'].between(1, 5)]
    rows_dropped_rating = initial_rows - len(df)
    if rows_dropped_rating > 0:
         print(f"Dropped {rows_dropped_rating} rows with invalid ratings (not between 1-5).")
    print(f"Shape after normalizing rating: {df.shape}")

    # 3. Remove duplicates based on review text and millet type
    initial_rows = len(df)
    df.drop_duplicates(subset=['review_text', 'millet_type'], keep='first', inplace=True)
    rows_dropped_dup = initial_rows - len(df)
    if rows_dropped_dup > 0:
        print(f"Dropped {rows_dropped_dup} duplicate review entries.")
    print(f"Shape after dropping duplicates: {df.shape}")

    # 4. Generate unique review_id
    df['review_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    print("Generated unique 'review_id' for each row.")

    # 5. Add timestamp
    df['processing_timestamp'] = datetime.now()

    # 6. Apply text cleaning to 'review_text' to create 'clean_review'
    print("Applying text cleaning and lemmatization to 'review_text'...")
    df['clean_review'] = df['review_text'].apply(clean_text)
    empty_clean_reviews = df['clean_review'].eq("").sum()
    if empty_clean_reviews > 0:
        print(f"Warning: {empty_clean_reviews} reviews resulted in an empty 'clean_review' after processing.")

    # Reorder columns for clarity (optional)
    # Ensure 'sentiment' column exists before including it
    base_cols = ['review_id', 'millet_type', 'platform', 'rating', 'review_text', 'clean_review']
    if 'sentiment' in df.columns:
        base_cols.append('sentiment')
    base_cols.append('processing_timestamp')

    other_cols = [col for col in df.columns if col not in base_cols]
    final_cols = base_cols + other_cols
    df = df[final_cols]

    print("Preprocessing finished.")
    return df

def save_processed_data(df, csv_path):
    """Saves the processed DataFrame to the current directory."""
    output_abs_path = os.path.abspath(csv_path)
    print(f"Attempting to save processed data to: {output_abs_path}")
    try:
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"Successfully saved {len(df)} rows to {output_abs_path}")
    except Exception as e:
        print(f"Error saving CSV to {output_abs_path}: {e}")

if __name__ == "__main__":
    print("--- Starting Data Preprocessing Script ---")
    
    # Define current directory for input/output
    current_dir = os.getcwd()
    input_file_path = os.path.join(current_dir, INPUT_CSV)
    output_file_path = os.path.join(current_dir, OUTPUT_CSV)
    
    processed_df = preprocess_data(input_file_path)

    if processed_df is not None and not processed_df.empty:
        save_processed_data(processed_df, output_file_path)
        print("\n--- Preprocessing Script Completed ---")
        print(f"Output file: {output_file_path}")
        print("\nFirst 5 rows of processed data:")
        print(processed_df.head())
    else:
        print("\n--- Preprocessing Script Failed ---")
        print("No output file generated. Please check for errors above.")