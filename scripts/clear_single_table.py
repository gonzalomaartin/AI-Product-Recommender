from sqlalchemy import MetaData, Table

from src.database.db_utils import SessionLocal, Base, engine


def clear_single_table(table_name): 
    try: 
        metadata = MetaData()

        # Loading all the existing tables
        metadata.reflect(bind=engine)

        # Selecting the table
        product_table = Table(table_name, metadata)

        # Borro la tabla
        product_table.drop(engine)

    except Exception as e: 
        print(f"Exception while deleting table: {table_name} \n {e}")

if __name__ == "__main__": 
    clear_single_table("product-db")