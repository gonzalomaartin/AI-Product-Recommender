import aiohttp
import aiofiles
import os 
import asyncio 


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
    


if __name__ == "__main__":
    asyncio.run(download_image(
        "https://prod-mercadona.imgix.net/images/c1788076223b499bd260c6a03d89b087.jpg?fit=crop&h=300&w=300",
        ".",
        "prueba.jpg",
    ))