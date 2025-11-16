from scraper import llm_vlm_task
import asyncio

title1 = "Aceite de oliva 0,4º Hacendado"
ingredients1 = "Ingredientes: Aceite de oliva refinado y Aceite de Oliva Virgen Extra. Instrucciones de almacenamiento: El aceite a bajas temperaturas puede presentar enturbiamientos, que en nada afectan a sus características.."
folder_imgs1 = "../images/Aceite de oliva4241"

title2 = "Aceite de oliva 0,4º Hacendado"
ingredients2 = "Ingredientes: Ingredientes: Aceite de oliva refinado y Aceite de Oliva Virgen Extra."
folder_imgs2 = "../images/Aceite de oliva4240"

async def main():
    # Run both tasks concurrently
    await asyncio.gather(
        llm_vlm_task(title=title1, ingredients=ingredients1, folder_imgs=folder_imgs1),
        llm_vlm_task(title=title2, ingredients=ingredients2, folder_imgs=folder_imgs2)
    )

# Run the event loop
if __name__ == "__main__":
    asyncio.run(main())