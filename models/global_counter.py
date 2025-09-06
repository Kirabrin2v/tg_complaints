from sqlalchemy import Column, Integer, select
from db import Base, async_session
from utils.formatter import get_datetime


class GlobalCounter(Base):
    __tablename__ = "global_counter"

    last_globad_id = Column(Integer, primary_key=True)

    @classmethod
    async def get_id(cls) -> int:
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(select(cls).with_for_update())
                counter = result.scalar_one_or_none()

                if not counter:
                    counter = GlobalCounter(last_globad_id=1)
                    session.add(counter)

                    new_id = 1

                else:
                    counter.last_globad_id += 1
                    new_id = counter.last_globad_id

                return new_id
