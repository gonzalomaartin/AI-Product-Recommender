from dotenv import load_dotenv
import os 
import groq
import asyncio 
from pathlib import Path
import time 
import json

load_dotenv() 

GROK_API_KEY = os.getenv("GROK_API_KEY")
LLM_MODEL = os.getenv("REASONING_LLM_MODEL")
VLM_MODEL = os.getenv("VLM_MODEL")

client = groq.AsyncGroq(api_key=GROK_API_KEY)

BASE_DIR = Path(__file__).resolve().parent
prompt_file = BASE_DIR / "prompts"

with open(prompt_file / "BRAND_ALLERGIES_prod.txt", "r", encoding="utf-8") as file:
    llm_prompt = file.read()

with open(prompt_file / "VLM.txt", "r", encoding="utf-8") as file:
    vlm_prompt = file.read()


async def generate_model_response(model, messages, retries=5, delay=1):
    for attempt in range(retries):
        try:
            resp = await client.chat.completions.create(
                model = model,
                messages = messages,
            )
            print(resp)
            response = resp.choices[0].message.content.strip()
            if response.startswith("```"): 
                nutrition_text = response.split("\n")
                return json.loads("".join(nutrition_text[1:-1]))
            else: 
                return json.loads(response)
            
        except groq.RateLimitError as e:
            print(f"Rate limit hit. Retry {attempt+1}/{retries} in {delay}s...")
            await asyncio.sleep(delay)
            delay *= 2
        except groq.APIStatusError as e:
            print(f"API returned status {e.status_code}: {e.response}")
            # Maybe treat other statuses differently
            raise
        except groq.APIConnectionError as e:
            print("Failed to connect to Groq API:", e)
            raise

    print("Max retries reached. Could not complete request.")
    return None


async def perform_model_task(task, **kwargs): 
    t0 = time.perf_counter() 
    if task == "LLM": 
        model = LLM_MODEL 
        prompt = llm_prompt
        
        title = kwargs.get("title")
        description = kwargs.get("description")
        price_description = kwargs.get("price_description")
        if not title or not description or not price_description: 
            print("Missing information for LLM task")
            return None, 0
        
        user_info = """
        Ahora procesa:
        titulo: {titulo}
        descripcion: {descripcion}
        descripcion_precio: {descripcion_precio}
        """
        user_info = user_info.replace("{titulo}", title).replace("{descripcion}", description).replace("{descripcion_precio}", price_description)

        messages = [
            {"role": "system", "content": prompt}, 
            {"role": "user", "content": user_info}
            ]
    else: 
        model = VLM_MODEL 
        prompt = vlm_prompt
        image_urls = kwargs.get("image_urls")
        if image_urls is None: 
            print("Missing images for VLM task")
            return None, 0
        
    
        content_list = [{"type": "text", "text": prompt}]
        for url in image_urls[:5]: # Groq can only handle 5 images at max per request and the request needs to be < 20 MB
            content_list.append({
                "type": "image_url", 
                "image_url": {"url": url}
            })

        messages = [{"role": "user", "content": content_list}]

    resp = await generate_model_response(model, messages)
    t1 = time.perf_counter()
    compute_time = round(t1 - t0, 2)
    if task == "LLM": 
        print(f"Response from LLM: {resp}")
    else: 
        print(f"Response from VLM: {resp}")
    
    return resp, compute_time