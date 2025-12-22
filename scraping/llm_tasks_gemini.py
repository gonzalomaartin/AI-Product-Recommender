from dotenv import load_dotenv
import os 
from google import genai
from google.genai import types
import asyncio 
from pathlib import Path
import time 
import json
from pydantic import BaseModel 


load_dotenv() 

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VLM_MODEL = os.getenv("FAST_LLM_MODEL")
LLM_MODEL = os.getenv("LITE_LLM_MODEL")

client = genai.Client()

BASE_DIR = Path(__file__).resolve().parent
PROMPT_FOLDER = BASE_DIR / "prompts"

with open(PROMPT_FOLDER / "BRAND_ALLERGIES_prod.txt", "r", encoding="utf-8") as file:
    llm_prompt = file.read()

with open(PROMPT_FOLDER / "VLM.txt", "r", encoding="utf-8") as file:
    vlm_prompt = file.read()

class VLMResponse(BaseModel): 
    atributos: list[str]
    energia_kj: int | None 
    energia_kcal: int | None
    grasas_g: float | None
    grasas_saturadas: float | None 
    grasas_mono_g: float | None
    grasas_poli_g: float | None
    carbohidratos_g: float | None
    azucar_g: float | None
    fibra_g: float | None
    proteina_g: float | None
    sal_g: float | None 

class LLMResponse(BaseModel): 
    marca: str | None
    alergenos: list[str]
    precio_relativo: str | None



async def generate_model_response(model, user_prompt, config, retries=5, delay=1): # Receive an output parser and apply it 
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=config
            )
            print(response)
            # structured JSON output from the Pydantic model 
            response = response.text
            if response.startswith("```"): 
                nutrition_text = response.split("\n")
                return json.loads("".join(nutrition_text[1:-1]))
            else: 
                return json.loads(response)
            
        except Exception as e:
            print(f"Captured exception: {e}.\n Retry {attempt+1}/{retries} in {delay}s...")
            await asyncio.sleep(delay)
            delay *= 2

    print("Max retries reached. Could not complete request.")
    return None


async def perform_model_task(task, **kwargs): 
    t0 = time.perf_counter() 
    if task == "LLM": 
        model = LLM_MODEL 
        system_prompt = llm_prompt
        
        title = kwargs.get("title")
        description = kwargs.get("description")
        price_description = kwargs.get("price_description")
        if not title or not description or not price_description: 
            print("Missing information for LLM task")
            return None, 0
        
        contents = f"""Ahora procesa:
titulo: {title}
descripcion: {description}
descripcion_precio: {price_description}
"""

        config = types.GenerateContentConfig(
            temperature = 0.1, 
            system_instruction= system_prompt, 
            response_schema=LLMResponse
        )
    else: 
        model = VLM_MODEL 
        system_prompt = vlm_prompt
        folder_imgs = kwargs.get("folder_imgs")
        if folder_imgs is None: 
            print("Missing images for VLM task")
            return None, 0
        
    
        contents = ["Ahora extrae la información de las siguientes imagenes:"]
        # Read all image files inside the folder (any extension)
        image_files = sorted(list(Path(folder_imgs).glob("*.jpg")) + list(Path(folder_imgs).glob("*.jpeg")))
        for image_path in image_files[:5]:  # Limit to 5 images
            with open(image_path, "rb") as file:
                image = file.read()

            contents.append(
            types.Part.from_bytes(
                data=image,
                mime_type="image/jpeg"
            )
            )

        config = types.GenerateContentConfig(
            temperature = 0.1, # We don't want variability and imagination for this task, it needs to follow instructions
            response_schema = VLMResponse, # Pydantic model with the requested output
            system_instruction=system_prompt # prompt with the instructions for the model 
        )

    resp = await generate_model_response(model, contents, config)
    t1 = time.perf_counter()
    compute_time = round(t1 - t0, 2)
    if task == "LLM": 
        print(f"Response from LLM: {resp}")
    else: 
        print(f"Response from VLM: {resp}")
    
    return resp, compute_time