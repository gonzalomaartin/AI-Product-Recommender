from playwright.async_api import async_playwright, Page
import asyncio 
import random
import time 
import os 
import pandas as pd 
import aiohttp
import aiofiles
import re 
import nutritional_info_vlm
import product_info_llm
import json 
import time
from pprint import pprint, PrettyPrinter

PROD_CONCURRENCY = 1 
LLM_VLM_CONCURRENCY = 1
prod_semaphore = asyncio.Semaphore(PROD_CONCURRENCY)
llm_vlm_semaphore = asyncio.Semaphore(LLM_VLM_CONCURRENCY)
POSTAL_CODE = "46013"


async def fill_input(page: Page, value: str, wait_time: int = 2): 
    try: 
        element = await page.query_selector('[data-testid="postal-code-checker-input"]')
        await asyncio.sleep(wait_time)
        await element.fill("") #focusing and cleaning placeholder values 
        for ch in value: 
            await page.keyboard.type(ch)
            await asyncio.sleep(random.uniform(0.1, 0.2))

        return True
    
    except Exception as e: 
        print(f"Fill problem: {e}")
        await page.screenshot(path = "fill.png")
        return False


async def submit_form(page: Page, timeout: int = 2): 
    try: 
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle", timeout = timeout) #waiting for no more network requests
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

async def llm_vlm_task(description, folder_imgs): 
    async with llm_vlm_semaphore: 
        llm_task = product_info_llm.get_brand_allergens(description) 
        #as it's not awaited, the function doesn't get executed and returns a coroutine that gets passed to asyncio.gather()
        vlm_task = nutritional_info_vlm.parse_images(folder_imgs)
        
        # Run LLM + VLM concurrently for this product
        (prod_info, llm_duration), (nutr_info, vlm_duration) = await asyncio.gather(llm_task, vlm_task)
        #asyncio.gather() creates one subroutine for each task, and when one task gets awaited, the resources move to another coroutine
        #without any set priority. the coroutines are runned concurrently (not simultaneous) within the same OS thread. 
        return prod_info, llm_duration, nutr_info, vlm_duration
    
    
async def get_categories(page: Page): 
    item_info = []
    await asyncio.sleep(random.uniform(1, 3))
    await page.locator("a[href='/categories']").click() 
    await asyncio.sleep(random.uniform(1, 3))
    category_items = page.locator("li.category-menu__item")
    count = await category_items.count() 

    for i in range(count): 
        item = category_items.nth(i)
        category = await item.locator("label.subhead1-r").inner_text() 
        print(f"Category: {category}")
        await item.locator("button").first.click()
        await asyncio.sleep(random.uniform(0.5, 3))
        subcategory_items = page.locator("li.category-item")
        subcategory_count = await subcategory_items.count() 
        for j in range(subcategory_count): 
            subitem = subcategory_items.nth(j)
            subcategory = await subitem.locator("button.category-item__link").first.inner_text() 
            print(f"Subcategory: {subcategory}")
            list_items = await get_items(page, category, subcategory) 
            for i in range(len(list_items)): 
                # add the elements to the db 
                item_info.append(list_items[i])

    return item_info 
            

async def get_items(page: Page, category: str, subcategory: str): 
    list_items = []
    section_items = page.locator("[data-testid='section']")
    subsections = section_items.locator("h2.section__header")
    subsection_count = await subsections.count()
    for k in range(subsection_count): 
        subsection = subsections.nth(k)
        subsection_name = await subsection.inner_text()
        print(f"Subsection: {subsection_name}")
        section_items = section_items.locator("[data-testid='product-cell']")
        items_count = await section_items.count() 
        for z in range(items_count): 
            await section_items.nth(z).locator("button.product-cell__content-link").click()
            await asyncio.sleep(random.uniform(1, 3))
            item_url = page.url
            item_id = re.search(r"/(\d+)/", item_url).group(1)
            item_locator = page.locator("div.private-product-detail__content")
            item_description_locator = item_locator.locator("div.private-product-detail__left")
            item_description = await item_description_locator.get_attribute("aria-label")
            item_title = await item_locator.locator("h1.private-product-detail__description").inner_text()
            item_size_locator = item_locator.locator("div.product-format__size")
            item_size_spans_locator = item_size_locator.locator("span")
            item_size_texts = await item_size_spans_locator.all_text_contents()
            item_size = "".join(item_size_texts)
            item_price = await item_locator.locator("[data-testid='product-price']").first.inner_text()
            item_price = float(re.search(r"(\d+,\d+)", item_price).group(1).replace(",", "."))
            image_button = item_locator.locator("button.product-gallery__thumbnail")
            #filenames = []
            image_button_count = await image_button.count()
            for i in range(image_button_count): 
                await image_button.nth(i).click()
                await asyncio.sleep(random.uniform(0.5, 1.5))
                img = await item_description_locator.locator("[data-testid='image-zoomer-container'] img").get_attribute("src")
                print(img)
                filename = f"{i}.jpg"
                folder_imgs = f"../images/{subsection_name}{item_id}/"
                await download_image(img, folder_imgs, filename)
                #filenames.append(filename)

            item_description_llm = item_description.split("Instrucciones de uso")[0]
            item_price_pattern = re.search(r"(\d+,\d+)\s€/([\w\s]+)", item_size)
            item_price_measurement = float(item_price_pattern.group(1).replace(",", "."))
            item_units = item_price_pattern.group(2).strip()
            if item_units == "100 ml" or item_units == "100 g":
                if item_units == "100 ml": 
                    item_units = "L"
                else: 
                    item_units = "kg" 
                item_price_measurement *= 10
            item_weight = item_price / item_price_measurement #round it to the second decimal as floating point operations are not exact
            
            item_origin = re.search(r"Origen: (\w+)", item_description)
            if item_origin: 
                item_origin = item_origin.group(1).lower() 
            else: 
                item_origin = None

            prod_info, llm_duration, nutr_info, vlm_duration = await llm_vlm_task( description = item_description_llm, folder_imgs = folder_imgs)
            print(f"LLM call took {llm_duration:.2f} seconds.")
            print(f"VLM call took {vlm_duration:.2f} seconds.")

            item = {
                "product_ID": item_id, 
                "category": subcategory, 
                "subcategory": subsection_name,
                "description": item_description, 
                "title": item_title, 
                "item_size": item_size,     
                "item_price": item_price,
                "weight": item_weight, 
                "unit": item_units, 
                "price_per_unit": item_price_measurement,
                "image_path": folder_imgs,
                "origin": item_origin, 
                "product_link": item_url, 
                "llm_time": llm_duration, 
                "vlm_time": vlm_duration
            }
            #pp = PrettyPrinter(sort_dicts=False, indent=4)
            item.update(nutr_info)
            item.update(prod_info)
            print(json.dumps(item, indent=4, ensure_ascii=False)) # Prety printing the dictionary with all the information (one line for each key, value)
            #list_items.append(item)
            #list_items.update()
            # Add it to the databases (relational and vector)

            #await asyncio.sleep(5)

            await page.locator("[data-testid='modal-close-button']").click() 
            await asyncio.sleep(random.uniform(1, 3))


    return list_items


    

async def run_single(postal_code: str = POSTAL_CODE):
    async with async_playwright() as p: #doesn't need to close the browser manually
        browser = await p.chromium.launch(headless = False) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="es-ES"
        )
        page = await context.new_page()
        await page.goto("https://tienda.mercadona.es/", wait_until = "domcontentloaded")
        await asyncio.sleep(random.uniform(1, 2))
        try: 
            cookie_banner = page.locator('.cookie-banner__actions')  # or another selector
            await cookie_banner.get_by_role("button", name="Aceptar").click()
            await asyncio.sleep(random.uniform(1, 2))
        except Exception as e: 
            print(f"Cookie problem: {e}")
            await page.screenshot(path = "cookies.png")
        if not await fill_input(page, postal_code): #
            pass
        if not await submit_form(page): 
            pass 
        try: 
            item_info = await get_categories(page)
            time.sleep(5)
        except Exception as e: 
            print(e)

if __name__ == "__main__": 
    asyncio.run(run_single())