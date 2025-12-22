import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import ollama
from scraping.scraper_fast import engine, Product, vector_client, EMBEDDING_MODEL

# Create a synchronous session factory
SessionLocal = sessionmaker(bind=engine)

LLM_MODEL = "qwen2.5:7b-instruct" #change this to the Gemini one, which is inside the .env file


with open("prompts/LLM_SQL.txt", "r", encoding="utf-8") as file:
    llm_sql_propmt = file.read()

with open("prompts/LLM_decision.txt", "r", encoding="utf-8") as file:
    llm_decision_prompt = file.read()

def user_prompt_flow(user_prompt):
    """
    Implements the architecture for processing user queries.
    1. Captures user prompt.
    2. Performs vector search for top 5 products.
    3. Queries relational database for product details.
    4. Uses LLM to generate SQL query and executes it.
    5. Uses LLM to decide the best products.
    """

    # Step 1: Capture user prompt
    print(f"User Prompt: {user_prompt}")

    # Step 2: Perform vector search
    embedding = ollama.embed(model=EMBEDDING_MODEL, input=user_prompt)
    results = vector_client.query(
        query_embeddings=[embedding],
        n_results=5
    )
    top_ids = [result["id"] for result in results["documents"]]
    print(f"Top 5 product IDs from vector search: {top_ids}")

    # Step 3: Query relational database for product details
    products = []
    with SessionLocal() as session:
        products = session.query(Product).filter(Product.ID_producto.in_(top_ids)).all()
        print(f"Retrieved products: {products}")

    # Step 4: Use LLM to generate SQL query and execute it
    llm_sql_prompt = llm_sql_prompt.replace("{user_prompt}", user_prompt)
    sql_query = ollama.generate(model=LLM_MODEL, prompt=llm_sql_prompt)
    print(f"Generated SQL Query: {sql_query}")

    # Execute the SQL query
    with SessionLocal() as session: # TODO get only the IDs of the top 5 results 
        try:
            result = session.execute(text(sql_query))
            top_results = result.fetchmany(5)  # Fetch top 5 results
            print(f"Top 5 results from SQL query: {top_results}")

            # Append to products
            for row in top_results:
                products.append(row)
        except Exception as e:
            print(f"Error executing SQL query: {e}")

    #Execute a SQL query to get the import columns of the ID entries to pass to the decission_llm

    # Step 5: Use LLM to decide the best products
    llm_decision_prompt = llm_decision_prompt.replace("{user_propmt}", user_prompt)
    decision = ollama.generate(model=LLM_MODEL, prompt=llm_decision_prompt)
    print(f"LLM Decision: {decision}")

    return decision

if __name__ == "__main__":
    while True: 
        user_prompt = input("Que producto estas buscando (q para salir): ")
        if user_prompt == "q": 
            break 
        decision = user_prompt_flow(user_prompt)