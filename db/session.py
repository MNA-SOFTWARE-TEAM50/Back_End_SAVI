"""
Configuración de la base de datos
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

def _build_async_sync_urls(db_url: str) -> tuple[str, str]:
    """Devuelve (async_url, sync_url) con drivers correctos para SQLite/MySQL."""
    url = db_url.strip()
    # SQLite
    if url.startswith("sqlite"):
        async_url = url
        if "+aiosqlite" not in async_url:
            async_url = async_url.replace("sqlite://", "sqlite+aiosqlite://")
        # Sync URL sin aiosqlite
        sync_url = async_url.replace("+aiosqlite", "")
        return async_url, sync_url

    # MySQL
    if "+aiomysql" not in url and "+pymysql" in url:
        async_url = url.replace("+pymysql", "+aiomysql")
    elif "+aiomysql" in url:
        async_url = url
    else:
        # Si no especifica driver, asumir aiomysql para async y pymysql para sync
        async_url = url.replace("mysql://", "mysql+aiomysql://")
    sync_url = async_url.replace("+aiomysql", "+pymysql")
    return async_url, sync_url


ASYNC_DB_URL, SYNC_DB_URL = _build_async_sync_urls(settings.DATABASE_URL)

# Engine asíncrono
async_engine = create_async_engine(
    ASYNC_DB_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Engine síncrono para crear tablas y scripts
sync_engine = create_engine(
    SYNC_DB_URL,
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
    # Explicitly create the session and close it in a finally block.
    # Using `async with` here may attempt to close the session while
    # other connection work is in progress which can raise
    # IllegalStateChangeError. Creating the session and closing it in
    # a finally block avoids that race.
    session = AsyncSessionLocal()
    try:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    finally:
        # Ensure pooled connections are returned to the pool.
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
