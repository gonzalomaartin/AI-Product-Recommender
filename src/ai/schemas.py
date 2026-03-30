from pydantic import BaseModel, Field
from typing import Literal, List, Optional

class NutritionalInfo(BaseModel): 
    atributos: list[str]
    energia_kj: int | None 
    energia_kcal: int | None
    grasas_g: float | None
    grasas_saturadas_g: float | None 
    carbohidratos_g: float | None
    azucar_g: float | None
    fibra_g: float | None
    proteina_g: float | None
    sal_g: float | None 


class AllergenItem(BaseModel):
    nombre: str = Field(
        description="Nombre canónico del alérgeno (usar solo valores permitidos del enum)"
    )

    fuente: Literal["explicito", "inferido"] = Field(
        description="Indica si el alérgeno aparece explícitamente en los ingredientes o se ha inferido"
    )

    confianza: float = Field(
        ge=0.0,
        le=1.0,
        description="Nivel de confianza entre 0 y 1 sobre la detección del alérgeno"
    )

    evidencia: Optional[str] = Field(
        default=None,
        description="Palabra o fragmento exacto del texto donde se detecta el alérgeno"
    )

class Allergens(BaseModel): 
    alergenos: list[AllergenItem] = Field(
        "Lista de alérgenos detectados en el producto"
    )


class RelativePrice(BaseModel): 
    precio_relativo: Literal["muy barato", "barato", "estandar", "caro", "muy caro"]
    marca: str | None = Field(
        default=None,
        description="Marca del producto. Si no se puede identificar, devolver null (valor JSON)."
    )