from pydantic import BaseModel 

class NutritionalInfo(BaseModel): 
    atributos: list[str]
    energia_kj: int | None 
    energia_kcal: int | None
    grasas_g: float | None
    grasas_saturadas_g: float | None 
    grasas_mono_g: float | None
    grasas_poli_g: float | None
    carbohidratos_g: float | None
    azucar_g: float | None
    fibra_g: float | None
    proteina_g: float | None
    sal_g: float | None 

class Allergens(BaseModel): 
    alergenos: list[str]

class RelativePrice(BaseModel): 
    precio_relativo: str  
    marca: str | None