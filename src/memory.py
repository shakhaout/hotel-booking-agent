import os
# Suppress tokenizer parallelism warning and others
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import warnings
import logging
import transformers
warnings.filterwarnings("ignore")
logging.getLogger("transformers").setLevel(logging.ERROR)
transformers.logging.set_verbosity_error()

import chromadb
from chromadb.utils import embedding_functions
import uuid
from typing import List

class PreferenceMemory:
    def __init__(self, persist_path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_path)
        
        # Use a default embedding function (all-MiniLM-L6-v2 is standard)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name="user_preferences",
            embedding_function=self.embedding_fn
        )

    def add_preference(self, text: str):
        """Stores a user preference in the Vector DB."""
        print(f"DEBUG: Adding preference: {text}")
        self.collection.add(
            documents=[text],
            ids=[str(uuid.uuid4())],
            metadatas=[{"type": "preference"}]
        )

    def get_preferences(self, query_text: str = "", n_results: int = 5) -> List[str]:
        """Retrieves user preferences irrelevant of the query, or relevant to a query."""
        # If query is empty, we might want to fetch all, but vector search needs a query or we can peek.
        # For simplicity, if query is empty, we just query with a generic term "hotel preference".
        q = query_text if query_text else "hotel preference"
        
        results = self.collection.query(
            query_texts=[q],
            n_results=n_results
        )
        
        if results and results['documents']:
            return results['documents'][0]
        return []

    def get_all_preferences(self) -> List[str]:
        """Returns all stored preferences (up to a limit)."""
        # Chroma doesn't strictly support 'get all' efficiently without limit, 
        # but we can peek or get.
        count = self.collection.count()
        if count == 0:
            return []
        
        results = self.collection.get(limit=count)
        if results and results['documents']:
             return results['documents']
        return []

if __name__ == "__main__":
    # Test
    mem = PreferenceMemory()
    mem.add_preference("I prefer hotels with a gym")
    mem.add_preference("I need a quiet room")
    
    prefs = mem.get_preferences("gym")
    print("Retrieved prefs:", prefs)
