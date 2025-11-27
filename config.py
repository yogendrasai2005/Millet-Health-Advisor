import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    VECTOR_DB_PATH = "chroma_vector_db"  # Changed path
    CSV_PATH = "dataset_with_lexicon_sentiment.csv"  # Changed path