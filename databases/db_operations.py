from .db_utils import Base, engine, SessionLocal, Product, collection, EMBEDDING_MODEL
import ollama
import psycopg2
import asyncpg

print("🔄 db_operations.py is being executed...")

def init_db():
    try:
        Base.metadata.create_all(bind=engine)   # ← simple, sync, works perfectly
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize the database: {e}")
        raise


async def init_db_async(): 
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize the database: {e}")


def upload_product_relational_db(item_info: dict):
    db = SessionLocal()
    try:
        new_product = Product(**item_info)
        db.add(new_product)
        db.commit()          # ← normal sync commit, no await!
        db.refresh(new_product)
        print(f"✅ Successfully uploaded product {item_info['ID_producto']} to PostgreSQL")
    except Exception as e:
        db.rollback()
        print(f"Error uploading product: {e}")
        raise
    finally:
        db.close()

async def upload_product_relation_db_async(item_info: dict): 
    async with SessionLocal() as session: #try sync instead of async
        new_product = Product(**item_info)
        session.add(new_product)
        print("🔄 Adding product to the session...")
        await session.commit() # problem here 
        print(f"✅ Successfully uploaded product {item_info['ID_producto']} to the relational database.") 


def check_item_id(item_id): 
    # Check if item_id exists in the database
    db = SessionLocal()
    exists = db.query(Product).filter(Product.ID_producto == item_id).first() is not None
    db.close()
    return exists


def upload_product_vector_db(product_id, embedding): 
    collection.add(
        ids=[product_id],
        embeddings=embedding ,
        metadatas=[None]
    )
    print(f"✅ Successfully uploaded product {product_id} to the vector database.")


def compute_embedding(embedding_text): 
    item_embedding = ollama.embed(
        model = EMBEDDING_MODEL, 
        input = embedding_text
    )
    return item_embedding.embeddings