from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    select,
    delete,
    update,
)
from sqlalchemy.orm import declarative_base, relationship, joinedload
from db import Base, async_session
from utils.formatter import get_datetime


class User(Base):
    __tablename__ = "users"

    tg_id = Column(Integer, primary_key=True)
    username = Column(String)
    fullname = Column(String, nullable=True)
    date_create = Column(DateTime)
    date_update = Column(DateTime)

    complaints = relationship("Complaint", back_populates="user")
    blogger_requests = relationship("BloggerRequest", back_populates="user")
    buildings_requests = relationship("BuildingsRequest", back_populates="user")
    improvements_requests = relationship("ImprovementsRequest", back_populates="user")
    moderation_requests = relationship("ModerationRequest", back_populates="user")
    errors_requests = relationship("ErrorRequest", back_populates="user")

    moderator = relationship("Moderator", back_populates="user", uselist=False)

    @classmethod
    async def add_user(
        cls, tg_id: int, username: str, first_name: str = None, last_name: str = None
    ) -> None:
        async with async_session() as session:
            async with session.begin():
                now = get_datetime()
                first_name = first_name or ""
                last_name = last_name or ""
                user = cls(
                    tg_id=tg_id,
                    username=username,
                    fullname=f"{first_name} {last_name}",
                    date_create=now,
                    date_update=now,
                )

                session.add(user)

    @classmethod
    async def update_user(
        cls,
        tg_id: int,
        new_username: str,
        first_name: str = None,
        last_name: str = None,
        fullname: str = None,
    ) -> None:
        async with async_session() as session:
            async with session.begin():
                now = get_datetime()
                if not fullname:
                    first_name = first_name or ""
                    last_name = last_name or ""
                    fullname = f"{first_name} {last_name}"

                await session.execute(
                    update(cls)
                    .where(cls.tg_id == tg_id)
                    .values(username=new_username, date_update=now, fullname=fullname)
                )

    @classmethod
    async def get_user_by_id(cls, tg_id: int):
        async with async_session() as session:
            result = await session.execute(
                select(cls)
                .options(joinedload(cls.moderator), joinedload(cls.complaints))
                .where(cls.tg_id == tg_id)
            )
            return result.unique().scalar_one_or_none()

    @classmethod
    async def get_user_by_username(cls, username: str):
        # '''
        # Если человек, сохранённый в БД, долгое время не писал боту и
        # сменил юзернейм, а другой пользователь поставил себе предыдущий
        # юзернейм этого человека и написал боту, то в БД будет два человека
        # с одним юзернеймом
        # '''
        async with async_session() as session:
            result = await session.execute(
                select(cls)
                .options(joinedload(cls.moderator), joinedload(cls.complaints))
                .where(cls.username == username)
            )
            return result.unique().scalar_one_or_none()

    def __repr__(self):
        return f"<User {self.username}[{self.tg_id}]>"
