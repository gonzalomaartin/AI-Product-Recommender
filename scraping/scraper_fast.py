from playwright.async_api import async_playwright, Page
import asyncio 
import random
import time 
import os 
import pandas as pd 
import aiohttp
import aiofiles
import re 
from . import nutritional_info_vlm, product_info_llm
import json 
import time
from pprint import pprint, PrettyPrinter
from dotenv import load_dotenv
from databases.db_operations import upload_product_relational_db, check_item_id, init_db, upload_product_vector_db, compute_embedding
import traceback
import shutil 


load_dotenv()  # loads the .env file

WAIT_TIME = 0.25 #when clicling or performing an action, playwright needs some type to update the DOM
PROD_CONCURRENCY = 1 
LLM_VLM_CONCURRENCY = 1
prod_semaphore = asyncio.Semaphore(PROD_CONCURRENCY)
llm_vlm_semaphore = asyncio.Semaphore(LLM_VLM_CONCURRENCY)
POSTAL_CODE = "46013"
df = None


async def fill_input(page: Page, value: str, wait_time: int = WAIT_TIME): 
    try: 
        element = await page.query_selector('[data-testid="postal-code-checker-input"]')
        await asyncio.sleep(wait_time)
        await element.fill("") #focusing and cleaning placeholder values 
        for ch in value: 
            await page.keyboard.type(ch)
            #await asyncio.sleep(random.uniform(0.1, 0.2))

        return True
    
    except Exception as e: 
        print(f"Fill problem: {e}")
        await page.screenshot(path = "fill.png")
        return False


async def submit_form(page: Page, timeout: int = 0.2): 
    try: 
        await page.keyboard.press("Enter")
        #await page.wait_for_load_state("networkidle", timeout = timeout) #waiting for no more network requests
        return True
    
    except Exception as e: 
        print(f"Submit problem: {e}")
        await page.screenshot(path = "submit.png")
        return False
    
async def download_image(image_url: str, save_folder: str, filename: str):
    # ensure directory exists
    os.makedirs(save_folder, exist_ok=True)
    filepath = os.path.join(save_folder, filename)

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    content = await response.read()
                    async with aiofiles.open(filepath, 'wb') as f:
                        await f.write(content)
                    print(f"✅ Saved image: {filepath}")
                    return filepath
                else:
                    print(f"❌ Failed to download image from {image_url} (status {response.status})")
                    return None
    except Exception as e:
        print(f"❌ Error downloading image {image_url}: {e}")
        return None

async def llm_vlm_task(description, folder_imgs, price_description): 
    async with llm_vlm_semaphore: 
        llm_task = product_info_llm.get_brand_allergens(description, price_description) 
        #as it's not awaited, the function doesn't get executed and returns a coroutine that gets passed to asyncio.gather()
        vlm_task = nutritional_info_vlm.parse_images(folder_imgs)
        
        # Run LLM + VLM concurrently for this product
        (prod_info, llm_duration), (nutr_info, vlm_duration) = await asyncio.gather(llm_task, vlm_task)
        #asyncio.gather() creates one subroutine for each task, and when one task gets awaited, the resources move to another coroutine
        #without any set priority. the coroutines are runned concurrently (not simultaneous) within the same OS thread. 
        return prod_info, llm_duration, nutr_info, vlm_duration
    
    
async def get_categories(page: Page):
    global df  
    await asyncio.sleep(WAIT_TIME)
    await page.locator("a[href='/categories']").click() 
    await asyncio.sleep(WAIT_TIME)
    category_items = page.locator("li.category-menu__item")
    count = await category_items.count() 

    for i in range(count): 
        item = category_items.nth(i)
        category = await item.locator("label.subhead1-r").inner_text() 
        print(f"Category: {category}")
        await item.locator("button").first.click()
        await asyncio.sleep(WAIT_TIME)
        list_items = await get_items(page, category) 
        if df is None: 
            df = pd.DataFrame(list_items)
        else: 
            df_aux = pd.DataFrame(list_items)
            df = pd.concat([df, df_aux], ignore_index=True)
        
        print("✅ Batch of items saved into the DataFrame")


async def get_item_info(page, section_items, subcategory, subsection_name): 
    item_url = page.url
    item_id = re.search(r"/(\d+)/", item_url).group(1)
    # Check if item_id exists in the database
    exists = check_item_id(item_id)
    if exists:
        print(f"Item with ID {item_id} already in the database")
        await page.locator("[data-testid='modal-close-button']").click() 
        await asyncio.sleep(WAIT_TIME)
        return None 
    
    item_locator = page.locator("div.private-product-detail__content")
    item_description_locator = item_locator.locator("div.private-product-detail__left")
    item_description = await item_description_locator.get_attribute("aria-label")
    item_title = await item_locator.locator("h1.private-product-detail__description").inner_text()
    item_size_locator = item_locator.locator("div.product-format__size")
    item_size_spans_locator = item_size_locator.locator("span")
    item_size_texts = await item_size_spans_locator.all_text_contents()
    item_size_description = "".join(item_size_texts)
    item_price = await item_locator.locator("[data-testid='product-price']").first.inner_text()
    item_price = float(re.search(r"(\d+,\d+)", item_price).group(1).replace(",", "."))
    image_button = item_locator.locator("button.product-gallery__thumbnail")
    #filenames = []
    image_button_count = await image_button.count()
    folder_imgs = f"images/{subsection_name}{item_id}/"
    for i in range(image_button_count): 
        await image_button.nth(i).click()
        await asyncio.sleep(WAIT_TIME)
        img = await item_description_locator.locator("[data-testid='image-zoomer-container'] img").get_attribute("src")
        print(img)
        filename = f"{i}.jpg"
        await download_image(img, folder_imgs, filename)
        #filenames.append(filename)

    item_description_llm = item_description.split("Instrucciones")[0].strip() 
    item_size = item_size_description.split("|")[0]
    item_price_pattern = re.search(r"(\d+,\d+)\s€/([\w\s]+)", item_size_description)
    item_price_measurement = float(item_price_pattern.group(1).replace(",", "."))
    item_units = item_price_pattern.group(2).strip()
    if item_units == "100 ml" or item_units == "100 g":
        if item_units == "100 ml": 
            item_units = "L"
        else: 
            item_units = "kg" 
        item_price_measurement *= 10
    item_weight = round(item_price / item_price_measurement, 3)  # round to 2 decimal places
    
    item_origin = re.search(r"Origen: (\w+)", item_description)
    if item_origin: 
        item_origin = item_origin.group(1).lower() 
    else: 
        item_origin = None

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
    }

    return item_info
            

async def get_items(page: Page,subcategory: str): 
    list_items = []
    subsections = page.locator("[data-testid='section']")
    subsection_count = await subsections.count()
    for k in range(subsection_count): 
        subsection = subsections.nth(k)
        subsection_name = await subsection.locator("h2").first.inner_text()
        print(f"Subsection: {subsection_name}")
        section_items = subsection.locator("[data-testid='product-cell']")
        items_count = await section_items.count() 
        for z in range(items_count): 
            await section_items.nth(z).locator("[data-testid='open-product-detail']").click()
            await asyncio.sleep(WAIT_TIME)
            item_info = await get_item_info(page, section_items, subcategory, subsection_name)
            if item_info is None: 
                continue

            prod_info, llm_duration, nutr_info, vlm_duration = await llm_vlm_task(
                description = item_info["descripcion"],
                folder_imgs = item_info["folder_imgs"], 
                price_description = item_info["descripcion_precio"], 
                title = item_info["titulo"]
            )
            print(f"LLM call took {llm_duration:.2f} seconds.")
            print(f"VLM call took {vlm_duration:.2f} seconds.")
            
            shutil.rmtree(item_info["folder_imgs"], ignore_errors=True)
            print(f"Directory {item_info["folder_imgs"]} deleted successfully")
            del item_info["folder_imgs"]
            
            item_info["tiempo_computo"] = max(llm_duration, vlm_duration)

            for k, v in prod_info.items(): 
                if isinstance(v, list):
                    prod_info[k] = ", ".join(v) if v else "ninguno"

            for k, v in nutr_info.items(): 
                if isinstance(v, list):
                    nutr_info[k] = ", ".join(v) if v else "ninguno"

            

            item_embedding_text = {
                "Titulo producto": item_info["titulo"], 
                "Marca": prod_info["marca"], 
                "Categoria": subcategory, 
                "Subcategoria": subsection_name,
                "Descripcion": item_info["descripcion"], 
                "Peso": item_info["peso"], 
                "Origen": item_info["origen"],  
                "Alergenos": prod_info["alergenos"], 
            }

            item_info.update(nutr_info)
            item_info.update(prod_info)
            print(json.dumps(item_info, indent=4, ensure_ascii=False)) # Prety printing the dictionary with all the information (one line for each key, value)

            item_embedding_text.update(nutr_info)
            lines = []
            for k, v in item_embedding_text.items():
                if k == "precio_relativo": 
                    continue
                lines.append(f"{k}: {v}")

            embedding_text = "\n".join(lines)
            print(f"Embedding information: \n {json.dumps(embedding_text, indent=4, ensure_ascii=False)}")
            item_embedding = compute_embedding(embedding_text)

            upload_product_relational_db(item_info)

            list_items.append(item_info)

            upload_product_vector_db(item_info["ID_producto"], item_embedding)
            

            await page.locator("[data-testid='modal-close-button']").click() 
            await asyncio.sleep(WAIT_TIME)


    return list_items


    

async def run_single(postal_code: str = POSTAL_CODE):
    print("Running single")
    async with async_playwright() as p: #doesn't need to close the browser manually
        browser = await p.chromium.launch(headless = False) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="es-ES"
        )
        page = await context.new_page()
        await page.goto("https://tienda.mercadona.es/", wait_until = "domcontentloaded")
        await asyncio.sleep(WAIT_TIME) #Needed for the website to stabilize the network connection
        try: 
            cookie_banner = page.locator('.cookie-banner__actions')  # or another selector
            await cookie_banner.get_by_role("button", name="Aceptar").click()
            await asyncio.sleep(WAIT_TIME)
        except Exception as e: 
            print(f"Cookie problem: {e}")
            await page.screenshot(path = "cookies.png")
        if not await fill_input(page, postal_code): #
            pass
        if not await submit_form(page): 
            pass 
        try: 
            await get_categories(page)
        except Exception as e: 
            print(e)


if __name__ == "__main__": 
    print("Starting the program")
    # Debugging init_db execution
    print("🔄 Initializing the database...")
    try:
        init_db()
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize the database: {e}")
        exit(1)

    # Debugging run_single execution
    print("🔄 Starting the scraping process...")
    try:
        asyncio.run(run_single())
        print("✅ Scraping process completed successfully.")
    except Exception as e:
        print(f"❌ Scraping process failed: {e}")
        exit(1)

    df.to_csv("../databases/products.csv")
    print("✅ DataFrame saved to '../databases/products.csv'")