from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
import asyncio 
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Any, List, Dict

import src.ai.config as config 
from src.ai.prompts import load_all_prompts
from src.ai.schemas import NutritionalInfo, Allergens, RelativePrice


class AIOrchestrator: 
    def __init__(self): 
        prompts = load_all_prompts() 
        
        # 1. Pre-initialize Models
        price_llm = init_chat_model(config.RELATIVE_PRICE_MODEL, model_provider=config.RELATIVE_PRICE_PROVIDER, temperature=0)
        nutri_llm = init_chat_model(config.NUTRITIONAL_INFO_MODEL, model_provider=config.NUTRITIONAL_INFO_PROVIDER, temperature=0)
        aller_llm = init_chat_model(config.ALLERGENS_MODEL, model_provider=config.ALLERGENS_PROVIDER, temperature=0)

        # 2. Pre-build Chains (Structured Output where possible)
        self.price_chain = (
            ChatPromptTemplate.from_messages([
                SystemMessage(content=prompts[0]), 
                ("human", "Titulo: {title} \n Descripcion titulo: {price_description}")
            ]) | price_llm.with_structured_output(RelativePrice)
        )
        
        # Build nutritional chain with dynamic content support
        self.nutri_llm = nutri_llm.with_structured_output(NutritionalInfo)
        self.nutri_prompt = prompts[1]

        self.aller_parser = PydanticOutputParser(pydantic_object=Allergens)
        self.aller_chain = (
            ChatPromptTemplate.from_messages([
                SystemMessage(content=prompts[2]),
                ("human", "Descripcion del producto: {product_description} \n {format_instructions}")
            ]) | aller_llm | self.aller_parser
        )

    # 3. Declarative Retries
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: print(f"🔁 Retrying task... attempt {retry_state.attempt_number}")
    )
    async def _safe_invoke(self, chain, inputs):
        return await chain.ainvoke(inputs)
    
    async def extract_relative_price(self, title: str, price_description: str) -> RelativePrice:
        print("➡️ Extracting relative price")
        return await self._safe_invoke(self.price_chain, {"title": title, "price_description": price_description})
    
    async def extract_nutritional_info(self, image_urls: List[str]) -> NutritionalInfo:
        print("➡️ Extracting the nutritional information")
        urls = image_urls[:5] if image_urls else []

        # Build content with unpacked images
        content = [{"type": "text", "text": "Extrae la información nutricional"}]
        content.extend([{"type": "image_url", "image_url": {"url": url}} for url in urls])

        # Build chain with dynamic messages
        messages = [
            SystemMessage(content=self.nutri_prompt),
            HumanMessage(content=content)
        ]
        
        chain = ChatPromptTemplate.from_messages(messages) | self.nutri_llm
        return await chain.ainvoke({})
    
    async def extract_allergens(self, product_description: str) -> Allergens:
        print("➡️ Extracting the allergens")
        inputs = {
            "product_description": product_description,
            "format_instructions": self.aller_parser.get_format_instructions()
        }
        return await self._safe_invoke(self.aller_chain, inputs)


    async def orchestrate_AI_pipeline(self, relative_price: bool, nutritional_info: bool, allergens: bool, product_ID: str,  **kwargs) -> dict: 
        print(f"⚙️ Starting the AI pipeline for product {product_ID}")

        product_info = dict() 
        coroutines = []

        if relative_price: 
            coroutines.append(self.extract_relative_price(kwargs.get("title"), kwargs.get("price_description")))
        if nutritional_info: 
            coroutines.append(self.extract_nutritional_info(kwargs.get("image_urls")))
        if allergens: 
            coroutines.append(self.extract_allergens(kwargs.get("product_description")))
        
        results = await asyncio.gather(*coroutines, return_exceptions=True) # It returns an ordered list with the result of the coroutines
        for res in results: 
            if isinstance(res, Exception):  
                print("❌ Task failed in orchestration: {res}")
            product_info.update(res.model_dump())
            
        return product_info 