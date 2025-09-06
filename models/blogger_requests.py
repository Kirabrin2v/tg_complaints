from sqlalchemy import Column, String, Integer, select, update
from sqlalchemy.orm import relationship
from .custom_types import JsonList
from db import async_session
from utils.formatter import get_datetime
from datetime import datetime
from .requests_pattern import Request
from .global_counter import GlobalCounter


class BloggerRequest(Request):
    __tablename__ = "blogger_requests"

    nick = Column(String)
    request_type = Column(String)
    name = Column(String)
    years = Column(Integer)
    count_subscribers = Column(Integer)
    games = Column(JsonList)
    channel_hrefs = Column(JsonList)
    video_hrefs = Column(JsonList)

    moderator = relationship(
        "Moderator", back_populates="blogger_requests", uselist=False
    )
    user = relationship("User", back_populates="blogger_requests", uselist=False)

    @classmethod
    async def add_request(
        cls,
        user_id: int,
        nick: str,
        request_type: str,
        name: str,
        years: int,
        count_subscribers: int,
        games: list[str],
        channel_hrefs: list[str],
        video_hrefs: list[str],
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
                    name=name,
                    years=years,
                    count_subscribers=count_subscribers,
                    games=games,
                    channel_hrefs=channel_hrefs,
                    video_hrefs=video_hrefs,
                    moderator_id=moderator_id,
                    context=context,
                    is_active=is_active,
                )
                session.add(request)
                await session.flush()  # Получаем ID после INSERT
                return request.id
