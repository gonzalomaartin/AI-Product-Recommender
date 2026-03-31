from playwright.async_api import async_playwright, Page
import pandas as pd 
import asyncio 
import re 
from dotenv import load_dotenv
import shutil 
import json 

from src.ai.orchestrator import AIOrchestrator
from src.database.db_operations import upload_product_relational_db, check_item_id, init_db, upload_product_vector_db, compute_embedding
from src.scraper.utils import BASE_IMG_DIR, WAIT_TIME, POSTAL_CODE, accept_cookies, fill_input, submit_form, download_image, resize_image_url

load_dotenv()  # loads the .env file

processor = AIOrchestrator()

async def get_categories(page: Page):
    """Navigate to categories and scrape all products by category."""
    
    try:
        # Navigate to categories section
        await asyncio.sleep(WAIT_TIME)
        await page.locator("a[href='/categories']").click() 
        await asyncio.sleep(WAIT_TIME)
    except Exception as e:
        raise RuntimeError(f"❌ Failed to navigate to categories: {e}")
    
    # Extract category items
    try:
        category_items = page.locator("li.category-menu__item")
        count = await category_items.count() 
    except Exception as e:
        raise RuntimeError(f"❌ Failed to retrieve category items: {e}")

    # Iterate through categories
    for i in range(count):
        try:
            item = category_items.nth(i)
            category = await item.locator("label.subhead1-r").inner_text() 
            print(f"📂 Processing Category: {category}")
        except Exception as e:
            print(f"⚠️ Failed to extract category name at index {i}: {e}")
            continue
        
        try:
            await item.locator("button").first.click()
            await asyncio.sleep(WAIT_TIME)
        except Exception as e:
            print(f"⚠️ Failed to click category '{category}': {e}")
            continue
        
        try:
            await get_items(page, category) 
        except Exception as e:
            print(f"❌ Error processing items for category '{category}': {e}")
            raise


async def get_item_info(page, section_items, subcategory, subsection_name): 
    """Extract detailed product information from the product detail page."""
    
    # === EXTRACTING PRODUCT ID ===
    item_url = page.url
    item_id = re.search(r"/(\d+)", item_url).group(1) # If this wasn't succesful, an error would be raised previously
    
    # === EXTRACTING TITLE & DESCRIPTION ===
    try:
        item_locator = page.locator("div.private-product-detail__content")
        item_description_locator = item_locator.locator("div.private-product-detail__left")
        item_description = await item_description_locator.get_attribute("aria-label")
        item_title = await item_locator.locator("h1.private-product-detail__description").inner_text()
    except Exception as e:
        raise RuntimeError(f"❌ Failed to extract product title/description for ID {item_id}: {e}")
    
    # === EXTRACTING PRICE AND SIZE ===
    try:
        item_size_locator = item_locator.locator("div.product-format__size")
        item_size_spans_locator = item_size_locator.locator("span")
        item_size_texts = await item_size_spans_locator.all_text_contents()
        item_size_description = "".join(item_size_texts)
        
        item_price = await item_locator.locator("[data-testid='product-price']").first.inner_text()
        item_price = float(re.search(r"(\d+,\d+)", item_price).group(1).replace(",", "."))
    except Exception as e:
        raise RuntimeError(f"❌ Failed to extract size/price info for product {item_id}: {e}")
    
    # === EXTRACT & DOWNLOAD IMAGES ===
    folder_imgs = str(BASE_IMG_DIR / f"{subsection_name}{item_id}")
    try:
        div_images_locator = page.locator(".product-gallery-thumbnails img")
        item_images_urls = [resize_image_url(await img.get_attribute("src"), 900) for img in await div_images_locator.all()]
        for i, img_url in enumerate(item_images_urls): 
            filename = f"{i}.jpg"
            await download_image(img_url, folder_imgs, filename)
    except Exception as e:
        print(f"⚠️ Failed to download images for product {item_id}: {e}")
    
    # === PARSE PRICE & WEIGHT ===
    try:
        item_description_llm = item_description.split("Instrucciones")[0].strip() 
        item_size = item_size_description.split("|")[0]
        item_price_pattern = re.search(r"(\d+,\d+)\s€/([\w\s]+)", item_size_description)
        
        if not item_price_pattern:
            raise ValueError(f"Could not parse price pattern from: {item_size_description}")
        
        item_price_measurement = float(item_price_pattern.group(1).replace(",", "."))
        item_units = item_price_pattern.group(2).strip()
        
        if item_units == "100 ml" or item_units == "100 g":
            if item_units == "100 ml": 
                item_units = "L"
            else: 
                item_units = "kg" 
            item_price_measurement *= 10
        
        item_weight = round(item_price / item_price_measurement, 3)
    except Exception as e:
        raise RuntimeError(f"❌ Failed to parse price/weight for product {item_id}: {e}")
    
    # === EXTRACT ORIGIN (OPTIONAL) ===
    try:
        item_origin = re.search(r"Origen: (\w+)", item_description) 
        item_origin = item_origin.group(1).lower() if item_origin else None
    except Exception as e:
        print(f"⚠️ Failed to extract origin for product {item_id}: {e}")
        item_origin = None
    
    # === BUILD PRODUCT INFO DICTIONARY ===
    item_info = {
        "ID_producto": item_id, 
        "categoria": subcategory, 
        "subcategoria": subsection_name,
        "descripcion": item_description_llm, #only add the instructions if you want the user to ask how to use a given product
        "titulo": item_title, 
        "precio": item_price,
        "descripcion_precio": item_size_description,   
        "peso": item_weight, 
        "unidad": item_units, 
        "precio_por_unidad": item_price_measurement, #price normalized
        "origen": item_origin, 
        "link_producto": item_url,
        "folder_imgs": folder_imgs, 
        "image_urls": item_images_urls
    }

    return item_info
            

async def get_items(page: Page, subcategory: str): 
    """Extract all products from a category page."""
    list_items = []
    
    # === EXTRACT SUBSECTIONS ===
    try:
        subsections = page.locator("[data-testid='section']")
        subsection_count = await subsections.count()
    except Exception as e:
        raise RuntimeError(f"❌ Failed to retrieve subsections for category '{subcategory}': {e}")
    
    # === ITERATE THROUGH SUBSECTIONS ===
    for k in range(subsection_count):
        try:
            subsection = subsections.nth(k)
            subsection_name = await subsection.locator("h2").first.inner_text()
            print(f"\n📦 Processing Subsection: {subsection_name}")
        except Exception as e:
            print(f"⚠️ Failed to extract subsection name at index {k}: {e}")
            raise e 
        
        # === EXTRACT ITEMS IN SUBSECTION ===
        try:
            section_items = subsection.locator("[data-testid='product-cell']")
            items_count = await section_items.count()
            print(f"   Found {items_count} products in this subsection")
        except Exception as e:
            print(f"⚠️ Failed to count items in subsection '{subsection_name}': {e}")
            raise e
        
        # === ITERATE THROUGH ITEMS ===
        for z in range(items_count):
            # Click product to open details
            try:
                await section_items.nth(z).locator("[data-testid='open-product-detail']").click()
                await asyncio.sleep(WAIT_TIME)
            except Exception as e:
                print(f"   ⏭️ Product {z} out of stock or unavailable: {e}")
                continue
            
                # === EXTRACTING PRODUCT ID ===
            try:
                item_url = page.url
                item_id = re.search(r"/(\d+)", item_url).group(1)
            except Exception as e:
                raise RuntimeError(f"❌ Failed to extract product ID from URL '{page.url}': {e}")
            
            # === CHECKING IF PRODUCT EXISTS ON DB ===
            try:
                exists = check_item_id(item_id)
                if exists:
                    print(f"⏭️ Product ID {item_id} already in database, skipping...")
                    await page.locator("[data-testid='modal-close-button']").click() 
                    await asyncio.sleep(WAIT_TIME)
                    return None 
            except Exception as e:
                print(f"⚠️ Failed to check if product {item_id} exists: {e}")

            item_info = await get_item_info(page, section_items, subcategory, subsection_name)
            if item_info is None: 
                continue
            
            # Getting transformed and clean information
            llm_info = await processor.orchestrate_AI_pipeline(
                relative_price=True, 
                nutritional_info=True, 
                allergens=True, 
                product_ID=item_info["ID_producto"],
                title=item_info["titulo"], 
                price_description=item_info["descripcion_precio"], 
                image_urls=item_info["image_urls"], 
                product_description=item_info["descripcion"]
            )
            allergens_info = llm_info["alergenos"]
            del llm_info["alergenos"]

            shutil.rmtree(item_info["folder_imgs"], ignore_errors=True)
            print(f"📁 Directory {item_info["folder_imgs"]} deleted successfully")
            del item_info["folder_imgs"]
            del item_info["image_urls"]

            for k, v in llm_info.items(): 
                if isinstance(v, list) and (not v or isinstance(v[0], str)):
                    llm_info[k] = ", ".join(v) if v else ""

            # === PREPARING EMBEDDING TEXT ===
            item_embedding_text = {
                "Titulo producto": item_info["titulo"], 
                "Categoria": subcategory, 
                "Subcategoria": subsection_name,
                "Descripcion": item_info["descripcion"], 
                "Peso": item_info["peso"], 
                "Origen": item_info["origen"]
            }

            item_info.update(llm_info)
            print(json.dumps(item_info, indent=4, ensure_ascii=False)) # Prety printing the dictionary with all the information (one line for each key, value)

            item_embedding_text.update(llm_info)
            item_embedding_text["alergenos"] = ", ".join([x["nombre"] for x in allergens_info])

            lines = []
            for k, v in item_embedding_text.items():
                if k == "precio_relativo": 
                    continue
                lines.append(f"{k}: {v}")
            
            # === COMPUTING EMBEDDING ===
            embedding_text = "\n".join(lines)
            print(f"Embedding information: \n {json.dumps(embedding_text, indent=4, ensure_ascii=False)}")
            item_embedding = compute_embedding(embedding_text)

            # === UPLOADING TO VECTOR & RELATIONAL DB ===
            upload_product_relational_db(item_info, allergens_info)

            upload_product_vector_db(item_info["ID_producto"], item_embedding)
            
            await page.locator("[data-testid='modal-close-button']").click() 
            await asyncio.sleep(WAIT_TIME)
    

async def run_single(url_start: str, postal_code: str = POSTAL_CODE):
    print("Running single")
    async with async_playwright() as p: #doesn't need to close the browser manually
        browser = await p.chromium.launch(headless = False) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="es-ES"
        )

        page = await context.new_page()
        await page.goto(url_start, wait_until = "domcontentloaded")
        await asyncio.sleep(WAIT_TIME) #Needed for the website to stabilize the network connection

        # Troubleshooting to get started scraping 
        await accept_cookies(page)
        await fill_input(page, postal_code)
        await submit_form(page) 
        
        # Beginning the party 
        await get_categories(page)


if __name__ == "__main__": 
    # Debugging init_db execution
    print("🔄 Initializing the database...")
    try:
        init_db()
    except Exception as e:
        exit(1)
    
    # Debugging run_single execution
    print("🔄 Starting the scraping process...")
    try:
        asyncio.run(run_single("https://tienda.mercadona.es/"))
        print("✅ Scraping process completed successfully.")
    except Exception as e:
        print(f"❌ Scraping process failed: {e}")
        exit(1)

