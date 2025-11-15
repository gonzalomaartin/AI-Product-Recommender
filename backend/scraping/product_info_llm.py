import ollama 
import json
import asyncio

client = ollama.AsyncClient()

model = "qwen2.5:7b-instruct"
global_prompt = ""

with open("prompts/BRAND_ALLERGIES_prod.txt", "r", encoding = "utf-8") as file: 
    global_prompt = file.read() 



async def get_brand_allergens(title, ingredients): 
    prompt = global_prompt.replace("{title}", title).replace("{ingredients}", ingredients)
    response = await client.generate(model = model, prompt = prompt)
    print(response.response)
   
    if response.response.startswith("```json"): 
        nutrition_text = response.response.split("\n")
        return json.loads("".join(nutrition_text[1:-1]))
    else: 
        return json.loads(response.response)



if __name__ == "__main__": 
    title = "Cereales copos de maíz Corn Flakes Hacendado 0% azúcares añadidos"
    ingredients = "Ingredientes: Maíz  (98%), sal, antioxidante (extracto rico en tocoferoles), vitaminas (B3, B5, B8,  B1, B2, B6, B12, B9), mineral (hierro). Puede contener trazas de gluten,  leche, frutos de cáscara y soja."

    product_info = asyncio.run(get_brand_allergens(title, ingredients))

    print(product_info)