from sqlalchemy import Column, Integer, String, select, update
from sqlalchemy.orm import relationship
from .custom_types import JsonList
from db import async_session
from utils.formatter import get_datetime
from datetime import datetime
from .requests_pattern import Request
from .global_counter import GlobalCounter


class BuildingsRequest(Request):
    __tablename__ = "buildings_requests"

    nick = Column(String)
    request_type = Column(String)
    game = Column(String)
    photo_ids = Column(JsonList)
    video_ids = Column(JsonList)
    document_id = Column(String)
    pos = Column(JsonList)

    moderator = relationship(
        "Moderator", back_populates="buildings_requests", uselist=False
    )
    user = relationship("User", back_populates="buildings_requests", uselist=False)

    @classmethod
    async def add_request(
        cls,
        user_id: int,
        nick: str,
        request_type: str,
        game: str,
        photo_ids: list[str],
        video_ids: list[str],
        document_id: str = None,
        pos: list[int] = [],
        moderator_id: int = None,
        context: list[str] = [],
        is_active: bool = True,
        date_create: datetime = None,
    ) -> int:
        if not date_create:
            date_create = get_datetime()

        if not context:
            context = []

        async with async_session() as session:
            async with session.begin():
                request = cls(
                    global_id=await GlobalCounter.get_id(),
                    date_create=date_create,
                    nick=nick,
                    user_id=user_id,
                    request_type=request_type,
                    game=game,
                    photo_ids=photo_ids,
                    video_ids=video_ids,
                    document_id=document_id,
                    pos=pos,
                    moderator_id=moderator_id,
                    context=context,
                    is_active=is_active,
                )
                session.add(request)
                await session.flush()  # Получаем ID после INSERT
                return request.id
