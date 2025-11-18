import ollama 
import json
import asyncio
import time

client = ollama.AsyncClient()

model = "qwen2.5:7b-instruct"
global_prompt = ""

with open("prompts/BRAND_ALLERGIES_prod.txt", "r", encoding = "utf-8") as file: 
    global_prompt = file.read() 


#Async because LLM tasks have a lot of I/O operations, and we can switch resources to another coroutine
async def get_brand_allergens(description, price_description): 
    print("Calling the LLM...")
    t0 = time.perf_counter()
    prompt = global_prompt.replace("{descripcion}", description).replace("{descripcion_precio}", price_description)
    response = await client.generate(
        model = model, 
        prompt = prompt,  
        options={"device": "cuda", "dtype": "float16"}
    )
   
    t1 = time.perf_counter() 
    if response.response.startswith("```json"): 
        nutrition_text = response.response.split("\n")
        return json.loads("".join(nutrition_text[1:-1])), t1 - t0
    else: 
        return json.loads(response.response), t1 - t0



if __name__ == "__main__": 
    description = "Queso rallado especial fundir mezcla Hacendado. Alérgenos: Contiene leche y sus derivados (incluida la lactosa). Libre de huevos y productos a base de huevo. Libre de cereales que contengan gluten.. Ingredientes: Queso, Proteína de leche, Mantequilla, Almidones modificados, Nata de (vaca, oveja y cabra),Sal, Sales de fundido (E452, E340, E332, E330),Conservador (E-202), Aroma natural, Antiaglomerante (E460 ii).SIN GLUTEN, SIN HUEVO.. Instrucciones de almacenamiento: Envasado en atmósfera protectora. Conservar en refrigeración entre 2ºC y 8ºC ."
    product_info, llm_time = asyncio.run(get_brand_allergens(description))

    print(f"It took {llm_time:.2f} seconds to process the information")
    print(product_info)