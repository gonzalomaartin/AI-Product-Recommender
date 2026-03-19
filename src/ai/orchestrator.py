from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
import asyncio 
import logging 

import src.ai.config as config 
from src.ai.prompts import load_all_prompts
from src.ai.schemas import NutritionalInfo, Allergens, RelativePrice

logger = logging.getLogger(__name__)

RELATIVE_PRICE_PROMPT, NUTRITIONAL_INFO_PROMPT, ALLERGENS_PROMPT = load_all_prompts()


async def orchestrate_AI_pipeline(relative_price: bool, nutritional_info: bool, allergens: bool, product_ID: str,  **kwargs) -> dict: 
    print(f"Starting the AI pipeline for product {product_ID}")

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


async def extract_relative_price(title: str, price_description: str, max_attempts = 3, wait_time = 30) -> dict: 
    print("Extracting the relative price")
    attempts = 0

    llm = init_chat_model(config.RELATIVE_PRICE_MODEL, model_provider=config.RELATIVE_PRICE_PROVIDER, temperature=0)
    structured_llm = llm.with_structured_output(RelativePrice)

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=RELATIVE_PRICE_PROMPT), 
        ("human", "Titulo: {title} \n Descripcion titulo: {price_description}")
    ])
    chain = prompt | structured_llm 

    # Pass a single input mapping object
    input_object = {"title": title, "price_description": price_description}
    while attempts < max_attempts: 
        try: 
            return await chain.ainvoke(input_object)
        except Exception as e:
            attempts += 1
            logger.warning(f"Attempt {attempts} of extract_relative_price failed: {e}")
            if attempts >= max_attempts:
                logger.exception(f"extract_relative_price failed after {max_attempts} attempts")
                raise
            asyncio.sleep(wait_time)


async def extract_nutritional_info(image_urls: list[str], max_attempts = 3, wait_time = 30) -> dict: 
    print("Extracting the nutritional information")
    attempts = 0

    # Avoiding overflowing the context window with no extra information 
    if len(image_urls) > 5: 
        image_urls = image_urls[:5]

    llm = init_chat_model(config.NUTRITIONAL_INFO_MODEL, model_provider=config.NUTRITIONAL_INFO_PROVIDER, temperature=0)
    structured_llm = llm.with_structured_output(NutritionalInfo)

    system_msg = SystemMessage(content=NUTRITIONAL_INFO_PROMPT)
    human_msg = HumanMessage(
        content=[
            {"type": "text", "text": "Extrae la información nutricional"},
            *[{"type": "image_url", "image_url": {"url": url}} for url in image_urls]
        ]
    )
    prompt = ChatPromptTemplate.from_messages([
        system_msg, 
        human_msg
    ])

    chain = prompt | structured_llm
    while attempts < max_attempts: 
        try: 
            return await chain.ainvoke({})
        except Exception as e:
            attempts += 1
            logger.warning(f"Attempt {attempts} of extract_nutritional_info failed: {e}")
            if attempts >= max_attempts:
                logger.exception(f"extract_nutritional_info failed after {max_attempts} attempts")
                raise
            asyncio.sleep(wait_time)
     

async def extract_allergens(product_description: str, max_attempts = 3, wait_time = 30) -> dict: 
    print("Extracting the allergens")
    attempts = 0

    llm = init_chat_model(config.ALLERGENS_MODEL, model_provider=config.ALLERGENS_PROVIDER, temperature=0) 
    # Structured Output on an LLM is implemented as a tool and Llama3-70B hasn't been trained on tool calling and it fails
    parser = PydanticOutputParser(pydantic_object=Allergens) # Manual parser instead of a tool 

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=ALLERGENS_PROMPT),
        ("human", "Descripcion del producto: {product_description} \n {format_instructions}")
    ])
    chain = prompt | llm | parser
    while attempts < max_attempts:
        try:
            return await chain.ainvoke({
                "product_description": product_description, 
                "format_instructions": parser.get_format_instructions()
            })
        except Exception as e:
            attempts += 1
            logger.warning(f"Attempt {attempts} of extract_allernges failed: {e}")
            if attempts >= max_attempts:
                logger.exception(f"extract_allergens failed after {max_attempts} attempts")
                raise
            asyncio.sleep(wait_time)