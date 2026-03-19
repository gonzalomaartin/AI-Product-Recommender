from playwright.async_api import async_playwright, Page
import asyncio 
import json 

from src.scraper.playwright_scraper import submit_form, get_item_info

WAIT_TIME = 0.5

async def fill_input(page: Page, value: str, wait_time: int = WAIT_TIME): 
    try: 
        element = await page.query_selector('[data-testid="input"]')
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

async def run_single_scrape(url_start: str, postal_code: str = "46013"):
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
            item_info = await get_item_info(page, "", "", "")
            print(json.dumps(item_info, indent=4, ensure_ascii=False))
            return item_info
        except Exception as e: 
            print(e)
    



if __name__ == "__main__": 
    asyncio.run(run_single_scrape("https://tienda.mercadona.es/product/3505.2/14-sandia-baja-semillas-14-pieza"))