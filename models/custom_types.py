import json
from sqlalchemy.types import TypeDecorator, TEXT


class JsonList(TypeDecorator):
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return []

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return []
