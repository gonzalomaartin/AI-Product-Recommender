from src.database.db_utils import COLLECTION_NAME, vector_client

def clear_chromadb():
    try:
        vector_client.delete_collection(COLLECTION_NAME)
        vector_client.create_collection(COLLECTION_NAME)
        print("✅ Collection reset successfully.")
    except Exception as e:
        print(f"❌ Failed to reset collection: {e}")

if __name__ == "__main__":
    clear_chromadb()