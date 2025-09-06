from typing import List, Dict, Any, Callable


class EventBus:
    def __init__(self):
        self._subscribers = {}
        self.event_names = set()

    def subscribe(self, event_name: str, callback: Callable[..., Any]):
        if event_name in self._subscribers:
            self._subscribers[event_name].append(callback)
        else:
            self._subscribers[event_name] = [callback]

    async def publish(self, event_name: str, args: List[Any]):
        for callback in self._subscribers.get(event_name, []):
            await callback(*args)


event_bus = EventBus()
