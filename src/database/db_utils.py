from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
import chromadb
import os 
from pathlib import Path 


print("🔄 db_utils.py is being executed...")

load_dotenv() 

DATABASE_URL = os.getenv("DATABASE_URL")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


#engine = create_async_engine(DATABASE_URL)
#SessionLocal = async_sessionmaker(autoflush=True, bind=engine, expire_on_commit=False)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Ensure the parent directory exists
persist_directory = Path.cwd() / "data" / "chroma_db"
os.makedirs(os.path.dirname(persist_directory), exist_ok=True)

# Use persistent local directory
vector_client = chromadb.PersistentClient(path = persist_directory)
try:
    collection = vector_client.get_collection(COLLECTION_NAME)
except Exception:
    collection = vector_client.create_collection(COLLECTION_NAME)
    print(f"✅ Successfully created collection:  '{COLLECTION_NAME}'")
