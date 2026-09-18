from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine_options = {"echo": settings.DB_ECHO}
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_options.update(pool_size=5, max_overflow=10)

engine = create_async_engine(settings.DATABASE_URL, **engine_options)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
