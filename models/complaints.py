from sqlalchemy import Column, String, DateTime, select, update
from sqlalchemy.orm import relationship
from .custom_types import JsonList
from db import async_session
from utils.formatter import get_datetime
from datetime import datetime
from .requests_pattern import Request
from .global_counter import GlobalCounter


class Complaint(Request):
    __tablename__ = "complaints"

    nick = Column(String)
    violator_nick = Column(String)
    date_event = Column(DateTime)
    location = Column(String)
    description = Column(String)
    photo_ids = Column(JsonList)
    video_ids = Column(JsonList)

    moderator = relationship("Moderator", back_populates="complaints", uselist=False)
    user = relationship("User", back_populates="complaints", uselist=False)

    @classmethod
    async def add_complaint(
        cls,
        date_event: datetime,
        user_id: int,
        nick: str,
        violator_nick: str,
        request_type: str,
        location: str,
        description: str,
        photo_ids: list[str],
        video_ids: list[str],
        moderator_id: int = None,
        context: list = [],
        is_active: bool = True,
        date_create: datetime = None,
    ) -> int:
        if not date_create:
            date_create = get_datetime()

        if not context:
            context = []

        async with async_session() as session:
            async with session.begin():
                complaint = cls(
                    global_id=await GlobalCounter.get_id(),
                    date_create=date_create,
                    date_event=date_event,
                    nick=nick,
                    violator_nick=violator_nick,
                    user_id=user_id,
                    request_type=request_type,
                    location=location,
                    description=description,
                    photo_ids=photo_ids,
                    video_ids=video_ids,
                    moderator_id=moderator_id,
                    context=context,
                    is_active=is_active,
                )
                session.add(complaint)
                await session.flush()  # Получаем ID после INSERT
                return complaint.id
