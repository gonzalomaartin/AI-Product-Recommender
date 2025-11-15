from paddleocr import PaddleOCR
import os 
import re 
import ollama 
import json


# Initialize PaddleOCR
ocr = PaddleOCR(lang='es')  # 'es' = Spanish
client = ollama.Client()    
model = "qwen2.5:7b-instruct"
ocr_llm_prompt = ""

# Open the OCR_LLM.txt file and read its content into a string
with open("prompts/OCR_LLM.txt", "r", encoding="utf-8") as file:
    ocr_llm_prompt = file.read()

def parse_nutrition_llm(image_path): 
    files = os.listdir(image_path)
    files = [os.path.join(image_path, file) for file in files]
    print(files)
    full_ocr_text = ""
    for image in files: 
        result = ocr.predict(image)
        ocr_lines = result[0]["rec_texts"]
        text = " ".join(ocr_lines).lower()
        if not full_ocr_text: 
            full_ocr_text = text
        else: 
            full_ocr_text += "\n---\n" + text 

    prompt = ocr_llm_prompt
    prompt += "\n\n" + full_ocr_text

    response = client.generate(model = model, prompt = prompt)
    return json.loads(response.response)

if __name__ == "__main__":
    BASE_PATH = "../images/prueba"

    #nutrition_text = extract_nutrition_from_product_images(files)
    nutrition_text = parse_nutrition_llm(BASE_PATH)

    if nutrition_text:
        print("Nutrition info detected:")
        print(nutrition_text)
    else:
        print("No nutrition info found.")



"""
OCR through Computer Vision was tried out in the following script, but wasn't choosen for production, as has difficulties to capture text
in sections that are not line by line, like ingredients and it's difficult to know when does one section end and another starts. 

So, if choosen to use a local LLM to get the nutrtional information, ingredients and so on, as it has an inner OCR much powerful. 
Moreover, it allows for reasoning º tasks like selecting the image that contains the nutritional information and much more. 


There's a lot of null fields as there's a lot of text that is not recogized and the text that is recognized is not always accurate.
Also for getting the claims, it helps a lot the context which is something that CV based approaches can't handle. 
Moreover, it takes a lot of time to load the OCR module and get the OCR text, compared to the VLM inference on images. 
"""