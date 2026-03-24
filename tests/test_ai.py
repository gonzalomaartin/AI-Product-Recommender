import json 
import asyncio 
from src.ai.orchestrator import AIOrchestrator
from tests.test_scraper import run_single_scrape
import re

TEST_URL = "https://tienda.mercadona.es/product/22966/cereales-copos-maiz-corn-flakes-hacendado-0-azucares-anadidos-caja"

processor = AIOrchestrator()

async def test_ai(url, product_ID = None):
    if not product_ID: 
        product_ID = re.search(r"/(\d+)", url).group(1)
    item_info = await run_single_scrape(url)
    llm_info = await processor.orchestrate_AI_pipeline(
        relative_price=True, 
        nutritional_info=True, 
        allergens=True, 
        product_ID=product_ID,
        title=item_info["titulo"], 
        price_description=item_info["descripcion_precio"], 
        image_urls=item_info["image_urls"], 
        product_description=item_info["descripcion"]
    )
    print(json.dumps(llm_info, indent=4, ensure_ascii=False)) 
    return llm_info

if __name__ == "__main__": 
    asyncio.run(test_ai(TEST_URL))