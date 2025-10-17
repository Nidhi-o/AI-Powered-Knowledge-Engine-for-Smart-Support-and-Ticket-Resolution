import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import pickle
import os
import re

def manual_load_dotenv(dotenv_path=".env"):
    """
    Manually parses a .env file and sets environment variables.
    This version is more forgiving of formatting errors.
    """
    if not os.path.exists(dotenv_path):
        print(f"Warning: .env file not found at {dotenv_path}. Relying on system environment variables.")
        return

    with open(dotenv_path) as f:
        for line in f:
            line = line.strip()
            # Ignore comments and blank lines
            if not line or line.startswith('#'):
                continue
            
            # Use regex to find the first '=' and split, handling potential spaces
            match = re.match(r'^\s*([\w.-]+)\s*=\s*(.*?)?\s*$', line)
            if match:
                key, value = match.groups()
                # Remove surrounding quotes from the value if they exist
                if value and ((value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'"))):
                    value = value[1:-1]
                os.environ.setdefault(key, value)

def check_env_variables():
    """Checks if critical environment variables are set."""
    # We only need the GROQ key for the main app, but checking here ensures
    # the .env file is being loaded correctly.
    required_vars = [
        "GROQ_API_KEY",
        "GOOGLE_SHEETS_CREDENTIALS_BASE64",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("\n" + "="*80)
        print("ERROR: Missing Environment Variables".center(80))
        print("="*80)
        print(f"The following required variables are not set: {', '.join(missing_vars)}\n")
        print("Please check the following:")
        print("1. You have a `.env` file in the main project directory.")
        print("2. The `.env` file contains all the required variables (see `.env.example`).")
        print("3. The `.env` file is formatted correctly (NO blank lines, NO comments, NO quotes).")
        print("="*80 + "\n")
        exit() # Stop the script if configuration is missing

def create_and_save_index(corpus_file="corpus.xlsx"):
    """
    Reads a corpus from an Excel file, generates embeddings,
    and saves the FAISS index and corpus data.
    """
    print("Loading environment variables...")
    manual_load_dotenv() # Use the new robust loader
    check_env_variables() # Validate .env file immediately
    
    print(f"Reading corpus from {corpus_file}...")
    try:
        df = pd.read_excel(corpus_file)
    except FileNotFoundError:
        print(f"Error: The file '{corpus_file}' was not found.")
        print("Please make sure your corpus Excel file is in the same directory.")
        return

    if 'Query' not in df.columns or 'Solution' not in df.columns:
        print("Error: The Excel file must contain 'Query' and 'Solution' columns.")
        return

    queries = df['Query'].tolist()
    solutions = df['Solution'].tolist()

    print("Initializing embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Generating embeddings for the corpus... (This may take a moment)")
    embeddings = model.encode(queries, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')

    # FAISS index setup
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # Save the index
    faiss.write_index(index, "faiss_index.bin")
    print(f"FAISS index saved to 'faiss_index.bin' ({index.ntotal} vectors).")

    # Save the queries and solutions for later retrieval
    corpus_data = {"queries": queries, "solutions": solutions}
    with open("corpus_data.pkl", "wb") as f:
        pickle.dump(corpus_data, f)
    print("Corpus data saved to 'corpus_data.pkl'.")
    print("\nSetup complete! You can now run the Streamlit app.")

if __name__ == "__main__":
    create_and_save_index()

