
from pydantic import BaseModel as PydanticBaseModel

class SectionSchema(PydanticBaseModel):
    title: str
    content: str = ""
    index: int = 0


class TopicSchema(PydanticBaseModel):
    title: str
    description: str = ""
    duration: int = 0
    sections: list[SectionSchema] = []
    is_recommended: bool = False
