import chromadb
from chromadb.config import Settings
import os


persist_directory = "../databases/chroma_db"
os.makedirs(os.path.dirname(persist_directory), exist_ok=True)

# Use persistent local directory
vector_client = chromadb.PersistentClient(path = persist_directory)
# Specify the collection name you want to delete
collection_name = "products"

# Check if the collection exists before deleting
existing_collections = [col.name for col in vector_client.list_collections()]
if collection_name in existing_collections:
    vector_client.delete_collection(collection_name)
    print(f"✅ Collection '{collection_name}' has been successfully deleted.")
else:
    print(f"⚠️ Collection '{collection_name}' does not exist.")