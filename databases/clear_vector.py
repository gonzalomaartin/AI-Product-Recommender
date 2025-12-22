from databases.db_utils import collection

def clear_chromadb():
    try:
        # Check if the collection exists
        if collection is not None:
            # Retrieve all points in the collection
            items = collection.get(include=[])   # faster: do not fetch embeddings/documents
            ids = items["ids"]
            collection.delete(ids=ids)
            print("✅ Successfully cleared all data from the ChromaDB collection.")
        else:
            print("⚠️ No collection found. Ensure the collection is properly initialized.")
    except Exception as e:
        print(f"❌ Failed to clear ChromaDB: {e}")

if __name__ == "__main__":
    clear_chromadb()