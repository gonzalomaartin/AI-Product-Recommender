from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey

Base = declarative_base()

class Product(Base): # Explore if you're going to save it in one or two tables
    __tablename__ = "products"

    ID_producto = Column(String, primary_key=True, autoincrement=True)
    categoria = Column(String)
    subcategoria = Column(String)

    descripcion = Column(String)
    titulo = Column(String)
    precio = Column(Float)
    marca = Column(String)
    origen = Column(String)

    descripcion_precio = Column(String)
    peso = Column(Float)
    unidad = Column(String)
    precio_por_unidad = Column(Float)
    precio_relativo = Column(String)
    atributos = Column(String) 

    energia_kj = Column(Integer)
    energia_kcal = Column(Integer)
    grasas_g = Column(Float)
    grasas_saturadas_g = Column(Float)  
    carbohidratos_g = Column(Float)
    azucar_g = Column(Float)
    fibra_g = Column(Float)
    proteina_g = Column(Float)
    sal_g = Column(Float)

    link_producto = Column(String, unique = True)
    tiempo_computo = Column(Float)

    alergenos = relationship("ProductAllergen", back_populates="product")


class ProductAllergen(Base):
    __tablename__ = "product_allergens"

    ID_alergeno = Column(Integer, primary_key=True, autoincrement=True)
    ID_producto = Column(String, ForeignKey("products.ID_producto"), nullable=False)
    nombre = Column(String) 
    fuente = Column(String)  
    confianza = Column(Float)  
    evidencia = Column(String, nullable=True)  

    product = relationship("Product", back_populates="alergenos")