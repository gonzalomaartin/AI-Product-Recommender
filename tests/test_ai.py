import json 
import asyncio 
from src.ai.orchestrator import orchestrate_AI_pipeline
from tests.test_scraper import run_single

TEST_URL = "https://tienda.mercadona.es/product/22966/cereales-copos-maiz-corn-flakes-hacendado-0-azucares-anadidos-caja"

async def test_ai(url): 
    item_info = await run_single(url)
    llm_info = await orchestrate_AI_pipeline(
        relative_price=True, 
        nutritional_info=True, 
        allergens=True, 
        title=item_info["titulo"], 
        price_description=item_info["descripcion_precio"], 
        image_urls=item_info["image_urls"], 
        product_description=item_info["descripcion"]
    )
    print(json.dumps(llm_info, indent=4, ensure_ascii=False)) 
    return llm_info

if __name__ == "__main__": 
    asyncio.run(test_ai(TEST_URL))