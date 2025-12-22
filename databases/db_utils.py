from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, JSON, Float, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
import os 

print("🔄 db_utils.py is being executed...")


load_dotenv() 

DATABASE_URL = os.getenv("DATABASE_URL")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


EMBEDDING_MODEL = "bge-m3"

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


Base = declarative_base()
class Product(Base): # Explore if you're going to save it in one or two tables
    __tablename__ = "product-db"

    ID_producto = Column(String, primary_key=True)
    categoria = Column(String)
    subcategoria = Column(String)
    descripcion = Column(String)
    titulo = Column(String)
    precio = Column(Float)
    marca = Column(String)
    origen = Column(String)
    descripcion_precio = Column(String)
    peso = Column(Float)
    unidad = Column(String)
    precio_por_unidad = Column(Float)
    precio_relativo = Column(String)
    alergenos = Column(JSON)
    atributos = Column(JSON) 
    energia_kj = Column(Integer)
    energia_kcal = Column(Integer)
    grasas_g = Column(Float)
    grasas_saturadas_g = Column(Float)
    grasas_mono_g = Column(Float)
    grasas_poli_g = Column(Float) 
    carbohidratos_g = Column(Float)
    azucar_g = Column(Float)
    fibra_g = Column(Float)
    proteina_g = Column(Float)
    sal_g = Column(Float)
    link_producto = Column(String, unique = True)
    tiempo_computo = Column(Float)


# Ensure the parent directory exists
persist_directory = "databases/chroma_db"
os.makedirs(os.path.dirname(persist_directory), exist_ok=True)

# Use persistent local directory
vector_client = chromadb.PersistentClient(path = persist_directory)
existing_collections = [col.name for col in vector_client.list_collections()]
if COLLECTION_NAME in existing_collections:
    collection = vector_client.get_collection(COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' already exists. Using the existing collection.")
else:
    collection = vector_client.create_collection(COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' created successfully.")

