from logging import LoggerAdapter

from pydantic import BaseModel


class LoggerContext(BaseModel):
    component_name: str = ""
    class_name: str = ""
    object_id: int = -1


class PipelineAdapter(LoggerAdapter):
    def process(self, msg, kwargs):
        context: LoggerContext = kwargs.pop("context", self.extra["context"])
        prefix = "[{component_name}] {class_name} {object_id} => ".format(
            **context.dict()
        )
        msg = prefix + msg
        return msg, kwargs
