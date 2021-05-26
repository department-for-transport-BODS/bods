import enum


class ChoiceEnum(enum.Enum):
    @classmethod
    def choices(cls):
        return sorted([(key.value, key.name) for key in cls], key=lambda c: c[0])
