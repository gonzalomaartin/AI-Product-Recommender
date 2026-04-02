from fastapi import FastAPI  
import asyncio 


app = FastAPI() 


@app.get("/")
async def get_products(): 
    ... 