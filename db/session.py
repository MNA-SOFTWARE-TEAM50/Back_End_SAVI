"""
Configuración de la base de datos
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Engine asíncrono para MySQL
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Engine síncrono para crear tablas
sync_engine = create_engine(
    settings.DATABASE_URL.replace("+aiomysql", "+pymysql"),
    echo=settings.DEBUG,
    pool_pre_ping=True
)

# SessionLocal asíncrona
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# SessionLocal síncrona (para migraciones)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Base para los modelos
Base = declarative_base()


async def get_db():
    """
    Dependencia para obtener sesión de base de datos asíncrona
    
    Yields:
        AsyncSession: Sesión de base de datos asíncrona
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db_sync():
    """
    Dependencia para obtener sesión de base de datos síncrona (para scripts)
    
    Yields:
        Session: Sesión de base de datos síncrona
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
