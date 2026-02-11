import os
import uuid
import numpy as np
import redis
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.commands.search.field import TextField, VectorField
from sentence_transformers import SentenceTransformer

class RedisMemory:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.vector_dim = 384  # Dimension for all-MiniLM-L6-v2

        # Define Index Names
        self.pref_index = "idx:preferences"
        self.history_index = "idx:interactions"

        # Initialize Indices
        self._create_index(self.pref_index, "preference:")
        self._create_index(self.history_index, "interaction:")

    def _create_index(self, index_name, prefix):
        """Creates a Redis Vector Search Index if it doesn't exist."""
        try:
            self.redis_client.ft(index_name).info()
            print(f"Index {index_name} already exists.")
        except:
            print(f"Creating index {index_name}...")
            schema = (
                TextField("content"),
                VectorField(
                    "embedding",
                    "FLAT", # Use HNSW for production with millions of items
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.vector_dim,
                        "DISTANCE_METRIC": "COSINE",
                    },
                ),
            )
            definition = IndexDefinition(prefix=[prefix], index_type=IndexType.HASH)
            self.redis_client.ft(index_name).create_index(schema, definition=definition)

    def _get_embedding(self, text: str) -> bytes:
        """Generates vector embedding."""
        vector = self.encoder.encode(text).astype(np.float32).tobytes()
        return vector

    def add_preference(self, text: str):
        """Stores a static user preference."""
        key = f"preference:{uuid.uuid4()}"
        self.redis_client.hset(key, mapping={
            "content": text,
            "embedding": self._get_embedding(text)
        })

    def save_interaction(self, user_query: str, agent_response: str):
        """Stores a conversation turn for RAG."""
        # We embed the user query to find it later when they ask similar things
        text = f"User asked: {user_query} | Agent answered: {agent_response}"
        key = f"interaction:{uuid.uuid4()}"
        self.redis_client.hset(key, mapping={
            "content": text,
            "embedding": self._get_embedding(user_query) # Embed query for relevance search
        })

    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """Searches BOTH Preferences and History for relevant context."""
        query_vector = self._get_embedding(query)

        # Helper to search an index
        def search_index(index_name):
            q = Query(f"*=>[KNN {top_k} @embedding $vec AS score]").return_fields("content", "score").dialect(2)
            res = self.redis_client.ft(index_name).search(q, query_params={"vec": query_vector})
            return [doc.content for doc in res.docs]

        # Fetch from both
        prefs = search_index(self.pref_index)
        history = search_index(self.history_index)

        context_parts = []
        if prefs:
            context_parts.append("USER PREFERENCES:\n" + "\n".join(f"- {p}" for p in prefs))
        if history:
            context_parts.append("RELEVANT PAST INTERACTIONS:\n" + "\n".join(f"- {h}" for h in history))
            
        return "\n\n".join(context_parts) if context_parts else "No relevant history found."