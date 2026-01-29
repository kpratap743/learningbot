from pinecone import Pinecone
import os

def get_pinecone_client():
    # Placeholder for Pinecone API Key
    api_key = os.getenv("PINECONE_API_KEY", "default_key_for_dev")
    return Pinecone(api_key=api_key)
