from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
import asyncio 

import src.ai.config as config 
from src.ai.prompts import load_all_prompts
from src.ai.schemas import NutritionalInfo, Allergens, RelativePrice

RELATIVE_PRICE_PROMPT, NUTRITIONAL_INFO_PROMPT, ALLERGENS_PROMPT = load_all_prompts()


async def orchestrate_AI_pipeline(relative_price: bool, nutritional_info: bool, allergens: bool, **kwargs) -> dict: 
    product_info = dict() 
    coroutines = []

    if relative_price: 
        coroutines.append(extract_relative_price(kwargs.get("title"), kwargs.get("price_description")))
    if nutritional_info: 
        coroutines.append(extract_nutritional_info(kwargs.get("image_urls")))
    if allergens: 
        coroutines.append(extract_allergens(kwargs.get("product_description")))
    
    results = await asyncio.gather(*coroutines) # It returns an ordered list with the result of the coroutines
    for res in results: 
        product_info.update(res.dict())
        
    return product_info 


async def extract_relative_price(title: str, price_description: str) -> dict: 
    llm = init_chat_model(config.RELATIVE_PRICE_MODEL, model_provider=config.RELATIVE_PRICE_PROVIDER, temperature=0)
    structured_llm = llm.with_structured_output(RelativePrice)

    prompt = ChatPromptTemplate.from_messages([
        ("system", RELATIVE_PRICE_PROMPT), 
        ("human", "Titulo: {title} \n Descripcion titulo: {price_description}")
    ])
    chain = prompt | structured_llm 
    return await chain.ainvoke(title=title, price_description=price_description)


async def extract_nutritional_info(image_urls: list[str]) -> dict: 
    llm = init_chat_model(config.NUTRITIONAL_INFO_MODEL, model_provider=config.NUTRITIONAL_INFO_PROVIDER, temperature=0)
    structured_llm = llm.with_structured_output(NutritionalInfo)

    system_msg = SystemMessage(content=RELATIVE_PRICE_PROMPT)

    human_msg = HumanMessage(
        content=[
            {"type": "text", "text": "Extrae la información nutricional"},
            *[{"type": "image_url", "image_url": {"url": url}} for url in image_urls]
        ]
    )
    messages = [system_msg, human_msg]
    return await structured_llm.ainvoke(messages)
     

async def extract_allergens(product_description: str) -> dict: 
    llm = init_chat_model(config.ALLERGENS_MODEL, model_provider=config.ALLERGENS_PROVIDER, temperature=0)
    structured_llm = llm.with_structured_output(Allergens)

    prompt = ChatPromptTemplate.from_messages([
        ("system", RELATIVE_PRICE_PROMPT), 
        ("human", "Descripcion del producto: {product_description}")
    ])
    chain = prompt | structured_llm 
    return await chain.ainvoke(product_description=product_description)