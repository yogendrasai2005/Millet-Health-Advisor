# setup_rag_vectorstore.py
# Loads the millet nutrition PDF, splits it, creates embeddings (using FREE local model),
# and saves to a local Chroma vector store.

import os
import time
from dotenv import load_dotenv

# --- LangChain Imports ---
try:
    from langchain_community.document_loaders import PyPDFLoader
    # Use external package with no spacy requirement for basic splitters
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    # Use FREE local embeddings instead of OpenAI
    from langchain_community.embeddings import HuggingFaceEmbeddings
    print("Successfully imported LangChain components.")
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please ensure required libraries are installed:")
    print("pip install langchain langchain-community pypdf chromadb tiktoken python-dotenv sentence-transformers")
    exit()

# --- Configuration ---
PDF_PATH = 'Nutritional_health_benefits_millets.pdf'
VECTORSTORE_PATH = 'chroma_vector_db'
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
# Using a FREE local embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Lightweight, effective model

# --- Initialize FREE Local Embedding Model ---
embeddings = None
try:
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},  # Use CPU to avoid GPU issues
        encode_kwargs={'normalize_embeddings': False}
    )
    print(f"Initialized FREE Local Embeddings ('{EMBEDDING_MODEL}').")
except Exception as e:
    print(f"Error initializing local embeddings: {e}.")
    print("Trying to install required packages...")
    try:
        import subprocess
        subprocess.check_call(["pip", "install", "sentence-transformers", "torch"])
        # Try again after install
        from langchain_community.embeddings import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        print("Successfully installed and initialized local embeddings.")
    except Exception as install_error:
        print(f"Failed to install required packages: {install_error}")
        exit()

def load_and_split_pdf(pdf_path, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """Loads PDF and splits it into text chunks."""
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {os.path.abspath(pdf_path)}")
        return None

    print(f"Loading PDF from: {pdf_path}")
    try:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            add_start_index=True,
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"Loaded and split PDF into {len(chunks)} text chunks.")

    except Exception as e:
        print(f"Error loading or splitting PDF: {e}")
        return None

    # Add page number metadata
    for chunk in chunks:
        if 'page' not in chunk.metadata:
            chunk.metadata['page'] = -1
        chunk.metadata['source_page'] = chunk.metadata.get('page', -1) + 1

    return chunks

def create_and_save_vectorstore(chunks, embedding_function, persist_directory):
    """Creates a Chroma vector store from chunks and saves it."""
    if not chunks or embedding_function is None:
        print("Error: Cannot create vector store without chunks or embedding function.")
        return None

    print(f"Creating vector store using {type(embedding_function).__name__}...")
    print(f"Embedding {len(chunks)} chunks. This may take a minute...")
    start_time = time.time()

    try:
        if os.path.exists(persist_directory):
            print(f"Note: Directory '{persist_directory}' already exists. Overwriting.")
            import shutil
            shutil.rmtree(persist_directory)

        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embedding_function,
            persist_directory=persist_directory
        )
        end_time = time.time()
        print(f"Vector store created and persisted successfully in {end_time - start_time:.2f} seconds.")
        print(f"Vector store saved to directory: {os.path.abspath(persist_directory)}")
        return vectorstore
    except Exception as e:
        print(f"Error creating Chroma vector store: {e}")
        return None

if __name__ == "__main__":
    print("--- Starting RAG Vector Store Setup Script (Using FREE Local Embeddings) ---")

    if embeddings is None:
        print("Error: Embedding model not initialized. Exiting.")
        exit()

    # 1. Load and Split PDF
    pdf_chunks = load_and_split_pdf(PDF_PATH)

    # 2. Create and Save Vector Store
    if pdf_chunks:
        vector_db = create_and_save_vectorstore(
            chunks=pdf_chunks,
            embedding_function=embeddings,
            persist_directory=VECTORSTORE_PATH
        )

        if vector_db:
            print("\n--- Vector Store Setup Complete ---")
            # Test the vector store
            try:
                print("\nTesting vector store with a sample query ('health benefits of ragi')...")
                test_query = "What are the key health benefits of ragi millet?"
                vectorstore_loaded = Chroma(persist_directory=VECTORSTORE_PATH, embedding_function=embeddings)
                results = vectorstore_loaded.similarity_search(test_query, k=2)
                if results:
                    print(f"Found {len(results)} relevant chunks for query: '{test_query}'. Snippet from first chunk:")
                    print("-" * 20)
                    print(f"Source Page: {results[0].metadata.get('source_page', 'N/A')}")
                    print(results[0].page_content[:400] + "...")
                    print("-" * 20)
                else:
                    print("Test query returned no results.")
            except Exception as test_e:
                print(f"Error testing vector store: {test_e}")
        else:
            print("\n--- Vector Store Creation Failed ---")
    else:
        print("\n--- Script Failed: Could not load or split PDF ---")