# extract_sentiment_aspects_groq.py
# Uses LangChain and Groq LLM (trying gemma-7b-it)

import pandas as pd
import os
import json
from datetime import datetime
from tqdm import tqdm
import time
from dotenv import load_dotenv

# --- LangChain Imports ---
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic.v1 import BaseModel, Field, validator
from typing import Literal, Optional, List

# --- Groq LLM Configuration ---
# Make sure your GROQ_API_KEY is set as an environment variable
# Example (PowerShell in VS Code): $env:GROQ_API_KEY = 'your_new_key_here'
llm = None # Initialize llm to None
load_dotenv()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_KEY_INLINE = "your_inline_api_key_here"  # Set your inline API key here
if GROQ_API_KEY_INLINE:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY_INLINE
DEFAULT_GROQ_API_KEY = ""

if not os.getenv("GROQ_API_KEY"):
    print("!!! WARNING: GROQ_API_KEY environment variable NOT FOUND. Set it in your environment or in a .env file. !!!")

try:
    from langchain_groq import ChatGroq

    groq_api_key_env = os.getenv("GROQ_API_KEY")

    if not groq_api_key_env:
        print("!!! WARNING: GROQ_API_KEY environment variable NOT FOUND. Script will likely fail. !!!")
        print("Please set it in your terminal before running: $env:GROQ_API_KEY = 'your_key_here'")
    else:
        print("GROQ_API_KEY environment variable found.")

    print(f"DEBUG: Attempting to use Groq model: {GROQ_MODEL}") # Debug print

    llm = ChatGroq(
        model=GROQ_MODEL,
        temperature=0.1
        )
    print(f"Successfully initialized LLM via Groq: {GROQ_MODEL}")

except ImportError:
    print("Error: langchain-groq not installed. Run 'pip install langchain-groq'")
except Exception as e:
    print(f"Error initializing Groq LLM: {e}.")
    print(f"Model '{GROQ_MODEL}' might be invalid or decommissioned, or API key issue.")
    print("Ensure GROQ_API_KEY environment variable is set correctly.")

# --- Define File Names (in the current directory) ---
# (Keep these the same)
INPUT_CSV = 'final_processed_dataset.csv'
OUTPUT_CSV = 'millet_review_sentiments_groq.csv'
ERROR_LOG_CSV = 'sentiment_extraction_groq_errors.csv'

# --- Define the Desired Output Structure (Same as before) ---
class SentimentAspects(BaseModel):
    sentiment_label: Literal['positive', 'neutral', 'negative'] = Field(description="Overall sentiment of the review.")
    sentiment_score: float = Field(description="Confidence score (0.0 to 1.0) for the sentiment label. Estimate if model doesn't provide (e.g., 0.9 positive, 0.5 neutral, 0.1 negative).")
    taste_score: Optional[float] = Field(description="Score from 0.0 (bad taste) to 1.0 (good taste) if taste is mentioned, otherwise null.")
    texture_mentioned: Optional[bool] = Field(description="True if texture (e.g., soft, grainy, hard) is mentioned, otherwise null.")
    cooking_time_mention: Optional[Literal['fast', 'slow', 'average', 'not mentioned']] = Field(description="Mention of cooking time (fast, slow, average) or 'not mentioned'.")
    health_benefit_mentioned: Optional[bool] = Field(description="True if health benefits (e.g., good for diabetes, weight loss) are mentioned, otherwise null.")
    price_mentioned: Optional[bool] = Field(description="True if price or value for money is mentioned, otherwise null.")
    extracted_keywords: Optional[List[str]] = Field(description="List of 3-5 key adjectives or nouns describing the millet qualities mentioned.")

    @validator('sentiment_score', 'taste_score') # Keep V1 style for now
    def score_must_be_in_range(cls, v):
        if v is not None and not (0.0 <= v <= 1.0):
            print(f"Warning: Clamping score {v} to be within [0.0, 1.0]")
            return max(0.0, min(1.0, v))
        return v

# --- Create Prompt and Parser (Same as before) ---
parser = JsonOutputParser(pydantic_object=SentimentAspects)

prompt_template = """
Analyze the following customer review about a millet product.
Extract the overall sentiment and specific aspects mentioned based *only* on the review text provided.

Review Text:
"{review_text}"

{format_instructions}

Provide the output strictly as a JSON object matching the format instructions. If an aspect is not clearly mentioned, use null or appropriate default (e.g., 'not mentioned').
For sentiment_score, provide a confidence level between 0.0 and 1.0. If the model doesn't naturally provide one, estimate it (e.g., 0.9 for strong positive, 0.5 for neutral, 0.1 for strong negative).
For taste_score, map mentions like 'tasty', 'delicious' towards 1.0 and 'bad taste', 'bland' towards 0.0.
"""

prompt = ChatPromptTemplate.from_template(prompt_template).partial(
    format_instructions=parser.get_format_instructions()
)

# --- Create the LangChain Chain ---
if llm:
    sentiment_chain = prompt | llm | parser
else:
    sentiment_chain = None # Will be caught in main block

# --- Function to Process a Batch of Reviews (Same as before) ---
def process_batch(batch_df):
    results = []
    errors = []
    if not sentiment_chain:
        print("Sentiment chain not initialized. Cannot process batch.")
        for index, row in batch_df.iterrows():
             errors.append({'review_id': row['review_id'], 'error': 'LLM not initialized', 'review_text': row.get('clean_review', '')})
        return [], errors

    for index, row in tqdm(batch_df.iterrows(), total=len(batch_df), desc="Processing batch"):
        review_id = row['review_id']
        clean_review = row.get('clean_review', '')

        if not clean_review or pd.isna(clean_review) or len(clean_review.split()) < 2:
             continue

        try:
            output = sentiment_chain.invoke({"review_text": clean_review})
            output['review_id'] = review_id
            results.append(output)
            time.sleep(0.05) # 50ms delay

        except Exception as e:
            error_message = str(e)
            if "rate limit" in error_message.lower():
                print(f"\nRate limit likely hit. Waiting 20 seconds...")
                time.sleep(20)
                errors.append({'review_id': review_id, 'error': 'Rate Limit Hit - Skipped', 'review_text': clean_review})
            elif "decommissioned" in error_message.lower() or "model_not_found" in error_message.lower():
                 print(f"\nERROR: The model '{GROQ_MODEL}' is unavailable/decommissioned. Please update the script.")
                 errors.append({'review_id': review_id, 'error': f'Model Unavailable/Decommissioned: {GROQ_MODEL}', 'review_text': clean_review})
                 # Stop this batch if the model is definitively wrong
                 return results, errors
            else:
                 print(f"\nWarning: Error processing review_id {review_id}: {error_message}")
                 errors.append({'review_id': review_id, 'error': error_message, 'review_text': clean_review})

    return results, errors

# --- Main Processing Logic (Same as before) ---
if __name__ == "__main__":
    print("--- Starting Sentiment and Aspect Extraction Script (using Groq) ---")

    current_dir = os.getcwd()
    input_file_path = os.path.join(current_dir, INPUT_CSV)
    output_file_path = os.path.join(current_dir, OUTPUT_CSV)
    error_log_path = os.path.join(current_dir, ERROR_LOG_CSV)

    if not os.path.exists(input_file_path):
        print(f"Error: Input file not found: {input_file_path}")
        exit()

    if not sentiment_chain:
         print("Error: LLM Chain could not be initialized. Exiting.")
         print("Check API key environment variable and model name.")
         exit()

    print(f"Loading data from {input_file_path}...")
    df = pd.read_csv(input_file_path)
    if 'clean_review' not in df.columns:
        print("Error: 'clean_review' column not found. Run the cleaning script first.")
        exit()
    print(f"Loaded {len(df)} rows.")

    # Optional: Filter for testing
    # df = df.head(10)
    # print(f"Processing a sample of {len(df)} rows...")

    batch_size = 50
    all_results = []
    all_errors = []
    stop_processing = False # Flag to stop if model is wrong

    print(f"Processing reviews in batches of {batch_size}...")
    for i in range(0, len(df), batch_size):
        if stop_processing:
            print("Stopping processing due to previous model error.")
            break
        batch = df.iloc[i : i + batch_size]
        print(f"\nProcessing batch {i//batch_size + 1}/{(len(df)-1)//batch_size + 1}...")
        batch_results, batch_errors = process_batch(batch)
        all_results.extend(batch_results)
        all_errors.extend(batch_errors)

        # Check if a model decommission/not found error occurred in this batch
        if any('Model Unavailable/Decommissioned' in err.get('error','') for err in batch_errors):
            stop_processing = True # Set flag to stop after this batch finishes

        # (Optional periodic save remains the same)
        # ...

    print("\n--- Processing Complete ---")

    # (Saving results and errors logic remains the same)
    results_df = pd.DataFrame(all_results)
    errors_df = pd.DataFrame(all_errors)

    if not results_df.empty:
        try:
            results_df.to_csv(output_file_path, index=False, encoding='utf-8')
            print(f"Successfully extracted sentiment/aspects for {len(results_df)} reviews.")
            print(f"Saved results to: {output_file_path}")
            print("\nFirst 5 results:")
            print(results_df.head())
        except Exception as save_final_err:
            print(f"Error saving final results CSV: {save_final_err}")
    else:
        print("No results were successfully processed.")

    if not errors_df.empty:
        try:
            errors_df.to_csv(error_log_path, index=False, encoding='utf-8')
            print(f"\nEncountered {len(errors_df)} errors during processing.")
            print(f"Error details saved to: {error_log_path}")
        except Exception as save_error_err:
             print(f"Error saving error log CSV: {save_error_err}")
    else:
        print("\nNo errors encountered during processing.")