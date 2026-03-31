from sqlalchemy import MetaData, Table
import argparse

from src.database.db_utils import engine


def clear_single_table(table_name): 
    try: 
        metadata = MetaData()

        # Loading all the existing tables
        metadata.reflect(bind=engine)

        # Selecting the table
        product_table = Table(table_name, metadata)

        # Borro la tabla
        product_table.drop(engine)

        print(f"✅ Successfully deleted {table_name} from product_db database")

    except Exception as e: 
        print(f"Exception while deleting table: {table_name} \n {e}")

if __name__ == "__main__": 
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--table', 
        type=str, 
        default=None, 
        help="Table name inside product_db database to be deleted"
    )
    
    args = parser.parse_args()
    clear_single_table(args.table)