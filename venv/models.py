from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base, engine

# --------------------
# Modelos para o ORM (Object-Relational Mapping)
# --------------------

class Estimate(Base):
    """
    Modelo para representar um orçamento completo.
    """
    __tablename__ = "estimates"
    id = Column(Integer, primary_key=True, index=True)
    client = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("LineItem", back_populates="estimate")

class LineItem(Base):
    """
    Modelo para representar um item de linha dentro de um orçamento.
    """
    __tablename__ = "line_items"
    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id"))
    description = Column(String)
    qty = Column(Float)
    unit = Column(String)
    unit_price = Column(Float)
    labor_hours = Column(Float)
    estimate = relationship("Estimate", back_populates="items")

class Orcamento(Base):
    """
    Modelo para representar um orçamento de reboco salvo.
    """
    __tablename__ = "orcamentos"
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String)
    valor = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)
