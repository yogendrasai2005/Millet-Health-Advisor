# recommender.py
# Loads millet summary data and recommends millets based on user preferences.

import pandas as pd
import os
import json
from datetime import datetime

# --- Define File Names (in the current directory) ---
MILLET_SUMMARY_CSV = 'millet_summary.csv'
LOG_CSV = 'recommendation_logs.csv' # File to log recommendations made

# --- Recommendation Weights (Adjust these based on importance) ---
WEIGHTS = {
    'sentiment': 0.4, # How positive are reviews overall?
    'rating': 0.1,    # How high is the average star rating? (Added)
    'health': 0.2,    # How well does it match health goals? (Placeholder for now)
    'taste': 0.15,    # How good is the taste score from reviews?
    'preference': 0.15,# How well does it match other preferences (texture, cooking)?
    # 'price': 0.0,   # Price component currently disabled (no price data in summary)
}

# --- Load Millet Summary Data ---
llm = None # Initialize llm to None
try:
    millet_summary_df = pd.read_csv(MILLET_SUMMARY_CSV)
    # Use millet_type as index for easy lookup
    if 'millet_type' in millet_summary_df.columns:
        millet_summary_df.set_index('millet_type', inplace=True)
        print(f"Loaded millet summary data for {len(millet_summary_df)} millet types.")
        # print("Available columns:", millet_summary_df.columns.tolist()) # Debug print
    else:
        print(f"Error: 'millet_type' column not found in {MILLET_SUMMARY_CSV}.")
        millet_summary_df = None
except FileNotFoundError:
    print(f"Error: Millet summary file not found at {os.path.abspath(MILLET_SUMMARY_CSV)}")
    millet_summary_df = None
except Exception as e:
    print(f"Error loading millet summary CSV: {e}")
    millet_summary_df = None

# --- Placeholder Functions (To be refined or replaced by LLM/RAG later) ---

def parse_user_input_simple(user_input_dict):
    """
    Placeholder: Directly uses a dictionary of preferences.
    Later, this can be replaced by an LLM call to parse free text.
    """
    print(f"Parsing user input: {user_input_dict}")
    default_prefs = {
        'health_goal': 'general',
        'taste_preference': 'any', # e.g., 'good', 'neutral', 'bad' based on taste_score range
        'texture_preference': 'any', # e.g., 'mentioned', 'not_mentioned'
        'cooking_preference': 'any', # e.g., 'fast', 'slow', 'average'
        # Add more preferences as needed
    }
    preferences = default_prefs | user_input_dict # Input overrides defaults
    return preferences

def meets_hard_constraints(millet_data, user_prefs):
    """ Checks hard constraints. Placeholder - add real rules later. """
    # Example: If user MUST have high calcium and millet is low (needs nutrition data)
    # if user_prefs.get('must_have_high_calcium') and millet_data.get('calcium_mg', 0) < 100:
    #     return False, "Low calcium content"
    return True, "Meets basic constraints"

def calculate_health_score(millet_data, user_prefs):
    """ Placeholder score based on health mentions or future nutrition data. """
    # Simple proxy: Use the percentage of reviews mentioning health benefits
    base_score = millet_data.get('health_benefit_mentioned', 0.0) # This is a pct (0-1)

    # VERY basic goal matching (replace with RAG/Nutrition DB later)
    goal = user_prefs.get('health_goal', 'general')
    if goal == 'weight_loss' and millet_data.name.lower() in ['foxtail millet', 'barnyard millet']: # Example
        base_score += 0.2
    elif goal == 'diabetes' and millet_data.name.lower() in ['foxtail millet', 'kodo millet']: # Example
        base_score += 0.2
    # Add more rules based on the PDF content

    return max(0.0, min(1.0, base_score)) # Ensure score is 0-1

def calculate_taste_score(millet_data, user_prefs):
    """ Score based on average taste score from reviews. """
    taste_pref = user_prefs.get('taste_preference', 'any')
    millet_taste_score = millet_data.get('taste_score', 0.5) # Default to neutral if missing

    # You could add logic here: if user wants 'good' taste, give higher weight to scores > 0.7 etc.
    # For now, just return the average score directly.
    return millet_taste_score

def calculate_preference_score(millet_data, user_prefs):
    """ Score based on texture, cooking time mentions matching preference. """
    score = 0.0
    # Example: Texture preference (simple match on mention)
    texture_pref = user_prefs.get('texture_preference', 'any')
    texture_mentioned_pct = millet_data.get('texture_mentioned', 0.0)
    if texture_pref == 'mentioned' and texture_mentioned_pct > 0.1: # If mentioned in >10% reviews
         score += 0.5
    elif texture_pref == 'not_mentioned' and texture_mentioned_pct <= 0.1:
         score += 0.5
    else: # 'any' preference matches anything reasonably well
        score += 0.25

    # Add similar logic for cooking_time_mention if data is available/extracted

    return max(0.0, min(1.0, score)) # Ensure score is 0-1

# --- Generate Explanation Template (Simple version) ---
def generate_explanation_template(millet_name, scores):
    """ Creates a basic reason string based on high scores. """
    reasons = []
    if scores['sentiment_score'] > 0.75:
        reasons.append(f"it's highly rated by users (avg sentiment: {scores['sentiment_score']:.2f})")
    elif scores['sentiment_score'] > 0.6:
         reasons.append(f"it receives generally positive reviews (avg sentiment: {scores['sentiment_score']:.2f})")

    if scores['rating_score'] > 4.0:
         reasons.append(f"has a high average star rating ({scores['rating_score']:.1f}/5)")

    if scores['health_score'] > 0.5: # Adjust threshold as needed
        reasons.append(f"matches well with your health focus (score: {scores['health_score']:.2f})")

    if scores['taste_score'] > 0.7:
        reasons.append(f"reviews often praise its taste (avg score: {scores['taste_score']:.2f})")

    if scores['preference_score'] > 0.6: # Adjust threshold
         reasons.append("fits your other preferences regarding texture/cooking")

    if not reasons:
        return f"{millet_name} offers a balanced profile according to reviews."
    else:
        return f"{millet_name} is a good choice because " + ", and ".join(reasons) + "."

# --- Main Recommendation Function ---
def recommend_millets(user_input_dict, top_k=3):
    """ Recommends millets based on input preferences and summary data. """
    if millet_summary_df is None or millet_summary_df.empty:
        print("Error: Millet summary data is not loaded or empty.")
        return [], {}

    user_prefs = parse_user_input_simple(user_input_dict)

    recommendations = []

    for millet_type, millet_data in millet_summary_df.iterrows():
        meets, reason = meets_hard_constraints(millet_data, user_prefs)
        if not meets:
            # print(f"Skipping {millet_type}: {reason}") # Optional logging
            continue

        # Calculate component scores (mostly normalized 0-1)
        score_sentiment = millet_data.get('sentiment_score', 0.5)
        score_rating = millet_data.get('avg_rating', 3.0) # Use original rating
        score_health = calculate_health_score(millet_data, user_prefs)
        score_taste = calculate_taste_score(millet_data, user_prefs)
        score_preference = calculate_preference_score(millet_data, user_prefs)
        # score_price = calculate_price_score(millet_data, user_prefs) # Add when available

        # Normalize avg_rating to 0-1 scale (assuming 1-5 rating range)
        normalized_rating = (score_rating - 1) / 4 if score_rating >= 1 else 0

        # Calculate final weighted score
        final_score = (
            WEIGHTS['sentiment'] * score_sentiment +
            WEIGHTS['rating'] * normalized_rating +
            WEIGHTS['health'] * score_health +
            WEIGHTS['taste'] * score_taste +
            WEIGHTS['preference'] * score_preference
            # + WEIGHTS['price'] * score_price # Add when available
        )

        # Store scores for explanation and ranking
        scores_for_explanation = {
            'final_score': round(final_score, 3),
            'sentiment_score': round(score_sentiment, 3),
            'rating_score': round(score_rating, 3), # Store original rating for explanation
            'health_score': round(score_health, 3),
            'taste_score': round(score_taste, 3),
            'preference_score': round(score_preference, 3)
            # 'price_score': score_price
        }
        recommendations.append({'millet_type': millet_type, 'scores': scores_for_explanation})

    # Sort by final score
    recommendations.sort(key=lambda x: x['scores']['final_score'], reverse=True)

    # Select top K and generate explanation template
    top_recommendations = []
    for i in range(min(top_k, len(recommendations))):
        rec = recommendations[i]
        millet_name = rec['millet_type']
        scores = rec['scores']
        explanation_template = generate_explanation_template(millet_name, scores)
        top_recommendations.append({
            'millet_type': millet_name,
            'score': scores['final_score'],
            'explanation_template': explanation_template,
            'details': scores
        })

    # --- Log the recommendation ---
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_input_json': json.dumps(user_input_dict),
        'parsed_prefs_json': json.dumps(user_prefs),
        # Log all candidates' scores for potential analysis
        'all_candidate_scores_json': json.dumps({rec['millet_type']: rec['scores'] for rec in recommendations}),
        'top_recommendations_json': json.dumps(top_recommendations)
    }
    log_recommendation(log_entry)


    return top_recommendations

def log_recommendation(log_entry):
    """Appends a recommendation log entry to the CSV file."""
    try:
        log_df = pd.DataFrame([log_entry])
        # Use column order from first entry if file exists, else use dict keys
        header = not os.path.exists(LOG_CSV)
        log_df.to_csv(LOG_CSV, index=False, header=header, mode='a', encoding='utf-8')
    except Exception as e:
        print(f"Warning: Error logging recommendation to {LOG_CSV}: {e}")


# --- Example Usage ---
if __name__ == "__main__":
    print("\n--- Running Recommendation Example ---")

    # Example user inputs (dictionary format for now)
    user_input_1 = {
        'health_goal': 'weight_loss'
    }
    user_input_2 = {
        'taste_preference': 'good', # We'll interpret this based on taste_score > threshold
        'texture_preference': 'mentioned'
    }
    user_input_3 = {} # General request

    print("\n--- Recommendation for User 1 (Weight Loss) ---")
    recommendations_1 = recommend_millets(user_input_1, top_k=3)
    if recommendations_1:
        for rec in recommendations_1:
            print(f"- {rec['millet_type']} (Score: {rec['score']})")
            print(f"  Reason: {rec['explanation_template']}")
            # print(f"  Details: {rec['details']}") # Optional: Print full score breakdown
    else:
        print("Could not generate recommendations for User 1.")


    print("\n--- Recommendation for User 2 (Taste/Texture) ---")
    recommendations_2 = recommend_millets(user_input_2, top_k=3)
    if recommendations_2:
        for rec in recommendations_2:
            print(f"- {rec['millet_type']} (Score: {rec['score']})")
            print(f"  Reason: {rec['explanation_template']}")
    else:
        print("Could not generate recommendations for User 2.")

    print("\n--- Recommendation for User 3 (General) ---")
    recommendations_3 = recommend_millets(user_input_3, top_k=3)
    if recommendations_3:
        for rec in recommendations_3:
            print(f"- {rec['millet_type']} (Score: {rec['score']})")
            print(f"  Reason: {rec['explanation_template']}")
    else:
         print("Could not generate recommendations for User 3.")

    print(f"\nRecommendation logs saved to {os.path.abspath(LOG_CSV)}")