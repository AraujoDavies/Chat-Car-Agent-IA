import os

from dotenv import load_dotenv
from sqlalchemy import (DECIMAL, Column, Float, Index, Integer, String, Text,
                        create_engine)
from sqlalchemy.orm import Session, declarative_base

load_dotenv()

engine = create_engine(
    os.getenv("DATABASE_URI")
)  # I'll use SQLite, if you want, can use other engine (but remember to install dependecies)
session = Session(engine)
Base = declarative_base()


class Cars(Base):
    __tablename__ = "tbl_cars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    marca = Column(String(45), nullable=False, index=True)
    modelo = Column(String(45), nullable=False, index=True)
    ano = Column(Integer, index=True)
    motorizacao = Column(String(45), nullable=False)
    tipo_combustivel = Column(String(45), nullable=False)
    cor = Column(String(45), nullable=False)
    quilometragem = Column(Integer, nullable=False)
    numero_de_portas = Column(Integer, nullable=False)
    transmissao = Column(String(45), nullable=False)
    categoria = Column(String(45), nullable=False, index=True)
    km_por_litro = Column(Float, nullable=False)
    preco = Column(DECIMAL(10, 2), nullable=False, index=True)
    descricao = Column(Text, nullable=False)

    __table_args__ = (Index("idx_car_brand_model", "marca", "modelo"),)

    def __repr__(self):
        return f"<Car id={self.id} modelo={self.modelo}>"

    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}


def drop_and_create_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
