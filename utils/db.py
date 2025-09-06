from sqlalchemy import Column, Integer, String, select
from db import Base, async_session


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=False)

    @classmethod
    async def create(cls, telegram_id: int, username: str):
        async with async_session() as session:
            async with session.begin():
                user = cls(telegram_id=telegram_id, username=username)
                session.add(user)

    @classmethod
    async def get_by_telegram_id(cls, telegram_id: int):
        async with async_session() as session:
            result = await session.execute(
                select(cls).where(cls.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    @classmethod
    async def search_by_username(cls, username_substr: str):
        async with async_session() as session:
            result = await session.execute(
                select(cls).where(cls.username.like(f"%{username_substr}%"))
            )
            return result.scalars().all()
