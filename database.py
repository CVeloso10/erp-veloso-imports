from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./estoque.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist and apply migrations."""
    Base.metadata.create_all(bind=engine)
    # Migrations for existing databases — add columns that may not exist yet
    _migrate_add_column("pedido_compra", "nome_identificador", "VARCHAR")
    _migrate_add_column("pedido_compra", "codigo_rastreio", "VARCHAR")
    _migrate_add_column("venda", "cliente_nome", "VARCHAR")
    _migrate_add_column("venda", "cliente_telefone", "VARCHAR")
    _migrate_add_column_with_default("venda", "status_pagamento", "VARCHAR", "CONFIRMADO")


def _migrate_add_column(table: str, column: str, coltype: str) -> None:
    """Add a column to an existing table if it doesn't already exist."""
    try:
        conn = engine.connect()
        result = conn.exec_driver_sql(
            f"PRAGMA table_info({table})"
        )
        cols = [row[1] for row in result]
        if column not in cols:
            conn.exec_driver_sql(
                f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"
            )
        conn.close()
    except Exception:
        pass


def _migrate_add_column_with_default(table: str, column: str, coltype: str, default: str) -> None:
    """Add a column with a default value to an existing table."""
    try:
        conn = engine.connect()
        result = conn.exec_driver_sql(
            f"PRAGMA table_info({table})"
        )
        cols = [row[1] for row in result]
        if column not in cols:
            conn.exec_driver_sql(
                f"ALTER TABLE {table} ADD COLUMN {column} {coltype} DEFAULT '{default}'"
            )
        conn.close()
    except Exception:
        pass
