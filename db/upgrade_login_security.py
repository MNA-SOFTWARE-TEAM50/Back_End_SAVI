"""
Upgrade script: add login security fields to users and create audit_logs table if missing.
This script is idempotent: safe to run multiple times.
"""
import os
import sys
from sqlalchemy import text, inspect, create_engine

# Ensure Back_End_SAVI root is on sys.path when invoked from workspace root
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from dotenv import load_dotenv

# Load env vars from Back_End_SAVI/.env explicitly
load_dotenv(os.path.join(BACKEND_ROOT, ".env"))


def column_exists_mysql(conn, table: str, column: str, schema: str | None = None) -> bool:
    q = text(
        """
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_NAME = :table
          AND COLUMN_NAME = :column
          {schema}
        LIMIT 1
        """.format(schema="AND TABLE_SCHEMA = :schema" if schema else "")
    )
    params = {"table": table, "column": column}
    if schema:
        params["schema"] = schema
    return conn.execute(q, params).first() is not None


def column_exists_sqlite(conn, table: str, column: str) -> bool:
    q = text("PRAGMA table_info(%s)" % table)
    res = conn.execute(q)
    for row in res:
        if row[1] == column:
            return True
    return False


def ensure_users_columns_mysql(conn, schema: str | None):
    added = []
    # failed_attempts INT NOT NULL DEFAULT 0
    if not column_exists_mysql(conn, "users", "failed_attempts", schema):
        conn.execute(text("ALTER TABLE users ADD COLUMN failed_attempts INT NOT NULL DEFAULT 0"))
        added.append("failed_attempts")
    # first_failed_at DATETIME NULL
    if not column_exists_mysql(conn, "users", "first_failed_at", schema):
        conn.execute(text("ALTER TABLE users ADD COLUMN first_failed_at DATETIME NULL"))
        added.append("first_failed_at")
    # is_locked TINYINT(1) NOT NULL DEFAULT 0
    if not column_exists_mysql(conn, "users", "is_locked", schema):
        conn.execute(text("ALTER TABLE users ADD COLUMN is_locked TINYINT(1) NOT NULL DEFAULT 0"))
        added.append("is_locked")
    # locked_at DATETIME NULL
    if not column_exists_mysql(conn, "users", "locked_at", schema):
        conn.execute(text("ALTER TABLE users ADD COLUMN locked_at DATETIME NULL"))
        added.append("locked_at")
    if not column_exists_mysql(conn, "users", "last_logout_at", schema):
        conn.execute(text("ALTER TABLE users ADD COLUMN last_logout_at DATETIME NULL"))
        added.append("last_logout_at")
    return added


def ensure_users_columns_sqlite(conn):
    added = []
    # SQLite no soporta ALTER TABLE ADD COLUMN IF NOT EXISTS convenientemente
    # pero sí permite ADD COLUMN si no existe; primero verificamos con PRAGMA
    if not column_exists_sqlite(conn, "users", "failed_attempts"):
        conn.execute(text("ALTER TABLE users ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0"))
        added.append("failed_attempts")
    if not column_exists_sqlite(conn, "users", "first_failed_at"):
        conn.execute(text("ALTER TABLE users ADD COLUMN first_failed_at DATETIME NULL"))
        added.append("first_failed_at")
    if not column_exists_sqlite(conn, "users", "is_locked"):
        conn.execute(text("ALTER TABLE users ADD COLUMN is_locked INTEGER NOT NULL DEFAULT 0"))
        added.append("is_locked")
    if not column_exists_sqlite(conn, "users", "locked_at"):
        conn.execute(text("ALTER TABLE users ADD COLUMN locked_at DATETIME NULL"))
        added.append("locked_at")
    if not column_exists_sqlite(conn, "users", "last_logout_at"):
        conn.execute(text("ALTER TABLE users ADD COLUMN last_logout_at DATETIME NULL"))
        added.append("last_logout_at")
    return added


def build_sync_url(db_url: str) -> str:
    url = db_url.strip()
    # SQLite
    if url.startswith("sqlite"):
        return url.replace("+aiosqlite", "")
    # MySQL
    if "+pymysql" in url:
        return url
    if "+aiomysql" in url:
        return url.replace("+aiomysql", "+pymysql")
    if url.startswith("mysql://"):
        return url.replace("mysql://", "mysql+pymysql://")
    return url


def create_audit_logs_table(conn, dialect: str, schema: str | None):
    if dialect == "mysql":
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id CHAR(36) PRIMARY KEY,
                action VARCHAR(50) NOT NULL,
                actor_user_id CHAR(36) NOT NULL,
                target_user_id CHAR(36) NULL,
                role_assigned VARCHAR(20) NULL,
                result VARCHAR(20) NOT NULL,
                detail VARCHAR(255) NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """
        ))
    elif dialect == "sqlite":
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                actor_user_id TEXT NOT NULL,
                target_user_id TEXT NULL,
                role_assigned TEXT NULL,
                result TEXT NOT NULL,
                detail TEXT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))
    else:
        # Generic ANSI
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id VARCHAR(36) PRIMARY KEY,
                action VARCHAR(50) NOT NULL,
                actor_user_id VARCHAR(36) NOT NULL,
                target_user_id VARCHAR(36) NULL,
                role_assigned VARCHAR(20) NULL,
                result VARCHAR(20) NOT NULL,
                detail VARCHAR(255) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))


def run_upgrade():
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./savi.db")
    sync_url = build_sync_url(db_url)
    engine = create_engine(sync_url, pool_pre_ping=True)
    with engine.begin() as conn:
        dialect = conn.dialect.name
        schema = None
        if dialect == "mysql":
            schema = conn.execute(text("SELECT DATABASE()")).scalar()
            added = ensure_users_columns_mysql(conn, schema)
        elif dialect == "sqlite":
            added = ensure_users_columns_sqlite(conn)
        else:
            inspector = inspect(conn)
            cols = {c["name"] for c in inspector.get_columns("users")}
            added = []
            if "failed_attempts" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0"))
                added.append("failed_attempts")
            if "first_failed_at" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN first_failed_at TIMESTAMP NULL"))
                added.append("first_failed_at")
            if "is_locked" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_locked BOOLEAN NOT NULL DEFAULT 0"))
                added.append("is_locked")
            if "locked_at" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN locked_at TIMESTAMP NULL"))
                added.append("locked_at")
            if "last_logout_at" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_logout_at TIMESTAMP NULL"))
                added.append("last_logout_at")

        # Create audit_logs table if missing via raw DDL
        create_audit_logs_table(conn, dialect, schema)

        return dialect, added


if __name__ == "__main__":
    dialect, added = run_upgrade()
    print(f"Upgrade complete on dialect={dialect}. Added columns: {added}")
