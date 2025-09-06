class BiMap:
    def __init__(self, mapping: dict):
        self.system_to_user = mapping
        self.user_to_system = {v: k for k, v in mapping.items()}

    def to_user(self, system_value: str) -> str:
        return self.system_to_user.get(system_value, system_value)

    def to_system(self, user_value: str) -> str:
        return self.user_to_system.get(user_value, user_value)

    def __contains__(self, item):
        return item in self.system_to_user
