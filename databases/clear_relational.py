from databases.db_utils import SessionLocal, Base, engine

def clear_postgresql():
    try:
        # Create a new session
        session = SessionLocal()

        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        print("✅ Successfully cleared all tables from the PostgreSQL database.")

        # Recreate the tables (optional, if you want to reset the schema)
        Base.metadata.create_all(bind=engine)
        print("✅ Successfully recreated the tables in the PostgreSQL database.")

        # Commit and close the session
        session.commit()
        session.close()
    except Exception as e:
        print(f"❌ Failed to clear PostgreSQL database: {e}")

if __name__ == "__main__":
    clear_postgresql()