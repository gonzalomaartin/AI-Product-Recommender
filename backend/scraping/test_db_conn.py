import psycopg2
from psycopg2 import OperationalError
import asyncio 
import asyncpg
from dotenv import load_dotenv
import os 

load_dotenv()  # loads the .env file

def test_sync_connection():
    try:
        conn = psycopg2.connect(
            dbname="testdb",
            user="postgre",
            password="24062004",
            host="localhost",
            port="5432"
        )
        print("✅ Synchronous connection successful!")
        conn.close()
    except OperationalError as e:
        print(f"❌ Failed to connect synchronously: {e}")


async def test_async_connection():
    try:
        # Replace with your database credentials
        conn = await psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )       
        print("✅ Asynchronous connection successful!")
        await conn.close()
    except Exception as e:
        print(f"❌ Failed to connect asynchronously: {e}")

def test_sync_connection_with_url():
    try:
        # Get the DATABASE_URL from environment variables
        database_url = os.getenv("DATABASE_URL")
        print(f"DATABASE_URL: {database_url}")

        # Use the database URL to connect
        conn = psycopg2.connect("postgresql://postgres:24062004@localhost:5432/Product-Recommender")
        print("✅ Synchronous connection using DATABASE_URL successful!")
        conn.close()
    except OperationalError as e:
        print(f"❌ Failed to connect synchronously using DATABASE_URL: {e}")
    except UnicodeDecodeError as e:
        print(f"❌ Encoding issue: {e}")

if __name__ == "__main__":
    test_sync_connection_with_url()
    test_sync_connection()
    asyncio.run(test_async_connection())