import asyncio
from collections import deque
from typing import Union
from telegram import Bot
import constants as const

# Очередь задач на удаление сообщений
_delete_queue = deque()
# Флаг и блокировка для запуска воркера
_worker_started = False
_worker_lock = asyncio.Lock()


async def _delete_worker(bot: Bot):
    global _delete_queue
    while True:
        if not _delete_queue:
            await asyncio.sleep(0.1)
            continue

        batch = []
        while _delete_queue and len(batch) < 20:
            batch.append(_delete_queue.popleft())

        tasks = [
            bot.delete_message(chat_id=chat_id, message_id=msg_id)
            for chat_id, msg_id in batch
        ]

        # Параллельно, но безопасно
        await asyncio.gather(*tasks, return_exceptions=True)

        # Ждём 1 секунду после каждой партии
        await asyncio.sleep(1)


async def delete_messages(chat_id: Union[int, str], message_ids: list[int]):
    """
    Удаляет сообщения партиями по 20 штук с задержкой между ними.

    :param bot: Экземпляр telegram.Bot или context.bot
    :param chat_id: Идентификатор чата
    :param message_ids: Список message_id для удаления
    """
    global _worker_started

    bot = const.bot

    async with _worker_lock:
        if not _worker_started:
            asyncio.create_task(_delete_worker(bot))
            _worker_started = True

    for message_id in message_ids:
        _delete_queue.append((chat_id, message_id))
