from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Configura o motor do banco de dados SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./orcamento.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_session():
    """
    Cria uma sessão de banco de dados e garante que ela seja fechada após o uso.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
