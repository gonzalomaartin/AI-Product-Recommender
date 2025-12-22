import ollama
import os 
import json 
import asyncio 
import time 
from pathlib import Path 

client = ollama.AsyncClient() 
model="qwen2.5vl" 

BASE_DIR = Path(__file__).resolve().parent
prompt_file = BASE_DIR / "prompts" / "VLM.txt"


with open(prompt_file, "r", encoding="utf-8") as file:
    prompt = file.read()


async def parse_images(folder_imgs): 
    print("Calling the VLM...")
    t0 = time.perf_counter() 
    files = os.listdir(folder_imgs)
    files = [os.path.join(folder_imgs, file) for file in files]
    images_data = []
    for file in files: 
        with open(file, "rb") as image_file:
            image_data = image_file.read()
            images_data.append(image_data)

    response = await client.generate(
        model= model, 
        prompt = prompt,
        images = images_data, 
        options={"device": "cuda", "dtype": "float16"}
    )
    
    t1 = time.perf_counter() 
    compute_time = t1 - t0
    if response.response.startswith("```json"): 
        nutrition_text = response.response.split("\n")
        return json.loads("".join(nutrition_text[1:-1])), round(compute_time, 2)
    else: 
        return json.loads(response.response), round(compute_time, 2)


if __name__ == "__main__": 
    BASE_PATH = "../images/prueba"
    nutrition_text, vlm_time = asyncio.run(parse_images(BASE_PATH))
    if nutrition_text:
        print(f"It took {vlm_time:.2f} seconds")
        print("Nutrition info detected:")
        print(nutrition_text)
    else:
        print("No nutrition info found.")