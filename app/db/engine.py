from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)  # ИСПРАВЛЕНО: добавлена фабрика сессий SessionLocal для импорта в app/db/queries.py


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session