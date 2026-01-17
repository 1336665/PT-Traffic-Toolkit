from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from app.config import settings


class Base(DeclarativeBase):
    pass


# Async engine for main application
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Synchronous engine for logging (runs in background thread)
# Convert async URL to sync URL
sync_database_url = settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")
sync_engine = create_engine(sync_database_url, echo=False)
SessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_delete_rule_columns(conn)


async def _ensure_delete_rule_columns(conn):
    """Ensure delete_rules table has new columns for Vertex-compatible rules."""
    if conn.dialect.name != "sqlite":
        return
    result = await conn.exec_driver_sql("PRAGMA table_info(delete_rules)")
    existing = {row[1] for row in result.fetchall()}
    columns = {
        "pause": "BOOLEAN DEFAULT 0",
        "only_delete_torrent": "BOOLEAN DEFAULT 0",
        "limit_speed": "INTEGER DEFAULT 0",
        "rule_type": "VARCHAR(20) DEFAULT 'normal'",
        "code": "TEXT DEFAULT ''",
    }
    for name, ddl in columns.items():
        if name not in existing:
            await conn.exec_driver_sql(f"ALTER TABLE delete_rules ADD COLUMN {name} {ddl}")


def init_sync_db():
    """Initialize sync database tables (for logger)"""
    Base.metadata.create_all(bind=sync_engine)
    _ensure_delete_rule_columns_sync()


def _ensure_delete_rule_columns_sync():
    if sync_engine.dialect.name != "sqlite":
        return
    with sync_engine.begin() as conn:
        result = conn.exec_driver_sql("PRAGMA table_info(delete_rules)")
        existing = {row[1] for row in result.fetchall()}
        columns = {
            "pause": "BOOLEAN DEFAULT 0",
            "only_delete_torrent": "BOOLEAN DEFAULT 0",
            "limit_speed": "INTEGER DEFAULT 0",
            "rule_type": "VARCHAR(20) DEFAULT 'normal'",
            "code": "TEXT DEFAULT ''",
        }
        for name, ddl in columns.items():
            if name not in existing:
                conn.exec_driver_sql(f"ALTER TABLE delete_rules ADD COLUMN {name} {ddl}")
