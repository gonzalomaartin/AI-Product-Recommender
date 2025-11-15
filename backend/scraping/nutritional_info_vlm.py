import ollama
import os 
import json 

client = ollama.Client() 
model="qwen2.5vl" 
with open("prompts/VLM.txt", "r", encoding="utf-8") as file:
    prompt = file.read()


def parse_images(image_path): 
    files = os.listdir(image_path)
    files = [os.path.join(image_path, file) for file in files]
    images_data = []
    for file in files: 
        with open(file, "rb") as image_file:
            image_data = image_file.read()
            images_data.append(image_data)

    response = client.generate(
        model= model, 
        prompt = prompt,
        images = images_data
    )
    
    if response.response.startswith("```json"): 
        nutrition_text = response.response.split("\n")
        return json.loads("".join(nutrition_text[1:-1]))
    else: 
        return json.loads(response.response)


if __name__ == "__main__": 
    BASE_PATH = "../images/prueba"
    nutrition_text = parse_images(BASE_PATH)
    if nutrition_text:
        print("Nutrition info detected:")
        print(nutrition_text)
    else:
        print("No nutrition info found.")