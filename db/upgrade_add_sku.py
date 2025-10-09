"""
Idempotent script to add SKU column to products and ensure unique index.
Works with MySQL and SQLite.
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv


def _to_sync_url(db_url: str) -> str:
    """Return a sync SQLAlchemy URL from a possibly-async one.

    - mysql+aiomysql -> mysql+pymysql
    - mysql:// -> mysql+pymysql://
    - sqlite+aiosqlite -> sqlite
    - sqlite:// stays as-is
    """
    url = db_url.strip()
    if url.startswith("mysql+"):
        # replace any async driver with pymysql
        url = url.replace("+aiomysql", "+pymysql")
    elif url.startswith("mysql://"):
        url = url.replace("mysql://", "mysql+pymysql://")
    elif url.startswith("sqlite+"):
        url = url.replace("+aiosqlite", "")
    # else: leave as-is
    return url


def main():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL no configurada en el entorno (.env)")

    engine = create_engine(_to_sync_url(database_url))

    with engine.begin() as conn:
        dialect = conn.dialect.name

        # 1) Agregar columna sku si no existe
        sku_exists = False
        if dialect == "mysql":
            res = conn.execute(text("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'products'
                AND COLUMN_NAME = 'sku'
            """))
            sku_exists = res.scalar() > 0
        else:
            # SQLite pragma
            res = conn.execute(text("PRAGMA table_info(products)"))
            for row in res.fetchall():
                if row[1] == 'sku':
                    sku_exists = True
                    break
        if not sku_exists:
            if dialect == "mysql":
                conn.execute(text("ALTER TABLE products ADD COLUMN sku VARCHAR(50) NULL"))
            else:
                conn.execute(text("ALTER TABLE products ADD COLUMN sku TEXT NULL"))

        # 2) Crear índice único para sku (si no existe)
        index_exists = False
        if dialect == "mysql":
            res = conn.execute(text("""
                SELECT COUNT(1) FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'products'
                  AND INDEX_NAME = 'ux_products_sku'
            """))
            index_exists = res.scalar() > 0
            if not index_exists:
                conn.execute(text("CREATE UNIQUE INDEX ux_products_sku ON products (sku)"))
        else:
            # SQLite: list indexes
            res = conn.execute(text("PRAGMA index_list(products)"))
            for row in res.fetchall():
                if row[1] == 'ux_products_sku':
                    index_exists = True
                    break
            if not index_exists:
                conn.execute(text("CREATE UNIQUE INDEX ux_products_sku ON products (sku)"))

    print("OK: SKU agregado/asegurado en products")


if __name__ == "__main__":
    main()
