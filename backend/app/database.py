from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine, event
from app.config import settings


class Base(DeclarativeBase):
    pass


def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and optimize SQLite for better concurrency."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=30000")  # 30 seconds timeout
    cursor.execute("PRAGMA cache_size=-64000")   # 64MB cache
    cursor.close()


# Async engine for main application
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args={"timeout": 30},  # Connection timeout
)

# Set up SQLite pragmas for async engine
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma_async(dbapi_connection, connection_record):
    _set_sqlite_pragma(dbapi_connection, connection_record)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Synchronous engine for logging (runs in background thread)
# Convert async URL to sync URL
sync_database_url = settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")
sync_engine = create_engine(
    sync_database_url,
    echo=False,
    connect_args={"timeout": 30, "check_same_thread": False},
)

# Set up SQLite pragmas for sync engine
event.listen(sync_engine, "connect", _set_sqlite_pragma)

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
        await _ensure_speed_limit_site_columns(conn)
        await _ensure_u2_magic_config_columns(conn)


# Whitelist of allowed column names and their DDL definitions for schema migrations
# This prevents potential SQL injection even though column names come from code
_DELETE_RULE_COLUMNS_WHITELIST = frozenset({
    "pause", "only_delete_torrent", "limit_speed", "rule_type", "code"
})

_SPEED_LIMIT_SITE_COLUMNS_WHITELIST = frozenset({
    "peerlist_enabled", "peerlist_url_template", "peerlist_cookie",
    "tid_regex", "peerlist_time_mode", "custom_announce_interval"
})

_U2_MAGIC_CONFIG_COLUMNS_WHITELIST = frozenset({
    "downloader_ids"
})


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
        # Security: Validate column name against whitelist
        if name not in _DELETE_RULE_COLUMNS_WHITELIST:
            raise ValueError(f"Column name '{name}' not in whitelist")
        if name not in existing:
            await conn.exec_driver_sql(f"ALTER TABLE delete_rules ADD COLUMN {name} {ddl}")


async def _ensure_speed_limit_site_columns(conn):
    """Ensure speed_limit_sites table has new peer list columns."""
    if conn.dialect.name != "sqlite":
        return
    result = await conn.exec_driver_sql("PRAGMA table_info(speed_limit_sites)")
    existing = {row[1] for row in result.fetchall()}
    columns = {
        "peerlist_enabled": "BOOLEAN DEFAULT 0",
        "peerlist_url_template": "VARCHAR(500) DEFAULT ''",
        "peerlist_cookie": "TEXT DEFAULT ''",
        "tid_regex": "VARCHAR(255) DEFAULT ''",
        "peerlist_time_mode": "VARCHAR(20) DEFAULT 'elapsed'",
        "custom_announce_interval": "INTEGER DEFAULT 0",
    }
    for name, ddl in columns.items():
        # Security: Validate column name against whitelist
        if name not in _SPEED_LIMIT_SITE_COLUMNS_WHITELIST:
            raise ValueError(f"Column name '{name}' not in whitelist")
        if name not in existing:
            await conn.exec_driver_sql(f"ALTER TABLE speed_limit_sites ADD COLUMN {name} {ddl}")


async def _ensure_u2_magic_config_columns(conn):
    """Ensure u2_magic_config table has downloader_ids column for multi-downloader support."""
    if conn.dialect.name != "sqlite":
        return
    result = await conn.exec_driver_sql("PRAGMA table_info(u2_magic_config)")
    existing = {row[1] for row in result.fetchall()}
    columns = {
        "downloader_ids": "TEXT DEFAULT ''",
    }
    for name, ddl in columns.items():
        # Security: Validate column name against whitelist
        if name not in _U2_MAGIC_CONFIG_COLUMNS_WHITELIST:
            raise ValueError(f"Column name '{name}' not in whitelist")
        if name not in existing:
            await conn.exec_driver_sql(f"ALTER TABLE u2_magic_config ADD COLUMN {name} {ddl}")


def init_sync_db():
    """Initialize sync database tables (for logger)"""
    Base.metadata.create_all(bind=sync_engine)
    _ensure_delete_rule_columns_sync()
    _ensure_speed_limit_site_columns_sync()
    _ensure_u2_magic_config_columns_sync()


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
            # Security: Validate column name against whitelist
            if name not in _DELETE_RULE_COLUMNS_WHITELIST:
                raise ValueError(f"Column name '{name}' not in whitelist")
            if name not in existing:
                conn.exec_driver_sql(f"ALTER TABLE delete_rules ADD COLUMN {name} {ddl}")


def _ensure_speed_limit_site_columns_sync():
    if sync_engine.dialect.name != "sqlite":
        return
    with sync_engine.begin() as conn:
        result = conn.exec_driver_sql("PRAGMA table_info(speed_limit_sites)")
        existing = {row[1] for row in result.fetchall()}
        columns = {
            "peerlist_enabled": "BOOLEAN DEFAULT 0",
            "peerlist_url_template": "VARCHAR(500) DEFAULT ''",
            "peerlist_cookie": "TEXT DEFAULT ''",
            "tid_regex": "VARCHAR(255) DEFAULT ''",
            "peerlist_time_mode": "VARCHAR(20) DEFAULT 'elapsed'",
            "custom_announce_interval": "INTEGER DEFAULT 0",
        }
        for name, ddl in columns.items():
            # Security: Validate column name against whitelist
            if name not in _SPEED_LIMIT_SITE_COLUMNS_WHITELIST:
                raise ValueError(f"Column name '{name}' not in whitelist")
            if name not in existing:
                conn.exec_driver_sql(f"ALTER TABLE speed_limit_sites ADD COLUMN {name} {ddl}")


def _ensure_u2_magic_config_columns_sync():
    if sync_engine.dialect.name != "sqlite":
        return
    with sync_engine.begin() as conn:
        result = conn.exec_driver_sql("PRAGMA table_info(u2_magic_config)")
        existing = {row[1] for row in result.fetchall()}
        columns = {
            "downloader_ids": "TEXT DEFAULT ''",
        }
        for name, ddl in columns.items():
            # Security: Validate column name against whitelist
            if name not in _U2_MAGIC_CONFIG_COLUMNS_WHITELIST:
                raise ValueError(f"Column name '{name}' not in whitelist")
            if name not in existing:
                conn.exec_driver_sql(f"ALTER TABLE u2_magic_config ADD COLUMN {name} {ddl}")
