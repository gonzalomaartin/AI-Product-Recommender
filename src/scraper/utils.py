import asyncio 
from playwright.async_api import Page
import aiohttp
import aiofiles
import os
from pathlib import Path
import pandas as pd 
import urllib.parse


WAIT_TIME = 0.5 # when clicling or performing an action, playwright needs some time to update the DOM
POSTAL_CODE = "46013"
BASE_DIR  = Path.cwd()
DF_PATH = BASE_DIR / "data" / "df_products.csv"
BASE_IMG_DIR = BASE_DIR / "data" / "images"



def load_dataframe():
    if DF_PATH.exists():
        try:
            df = pd.read_csv(DF_PATH)
            return df 
        except Exception as e:
            print(f"❌ Error loading dataframe: {e}")
            return None
    else:
        print("⚠️ Dataframe file not found.")
        return None



async def accept_cookies(page: Page): 
    try: 
        cookie_banner = page.locator('.cookie-banner__actions')  # or another selector
        await cookie_banner.get_by_role("button", name="Aceptar").click()
        await asyncio.sleep(WAIT_TIME)
    except Exception as e: 
        print(f"Cookie problem: {e}")
        await page.screenshot(path = "cookies.png")


async def fill_input(page: Page, value: str, wait_time: int = WAIT_TIME): 
    try: 
        element = await page.query_selector('[data-testid="postal-code-checker-input"]')
        await asyncio.sleep(wait_time)
        await element.fill("") #focusing and cleaning placeholder values 
        for ch in value: 
            await page.keyboard.type(ch)
            #await asyncio.sleep(random.uniform(0.1, 0.2))
    
    except Exception as e: 
        print(f"Input filling problem: {e}")
        await page.screenshot(path = "fill.png")
        return False


async def submit_form(page: Page, timeout: int = 0.2): 
    try: 
        await page.keyboard.press("Enter")
        #await page.wait_for_load_state("networkidle", timeout = timeout) #waiting for no more network requests
        await asyncio.sleep(WAIT_TIME) # Waiting for the changes to apply 
    
    except Exception as e: 
        print(f"Submiting form problem: {e}")
        await page.screenshot(path = "submit.png")
    

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
    

def resize_image_url(url, size=900):
    # 1. Parse the URL into components
    parsed_url = urllib.parse.urlparse(url)
    
    # 2. Extract query parameters into a dictionary
    query_params = urllib.parse.parse_qs(parsed_url.query)
    
    # 3. Update 'h' and 'w' values (stored as lists in parse_qs)
    query_params['h'] = [str(size)]
    query_params['w'] = [str(size)]
    
    # 4. Re-encode the query parameters
    new_query = urllib.parse.urlencode(query_params, doseq=True)
    
    # 5. Reconstruct the full URL
    new_url = urllib.parse.urlunparse(parsed_url._replace(query=new_query))
    
    return new_url