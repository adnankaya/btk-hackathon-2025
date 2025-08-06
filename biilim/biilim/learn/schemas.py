
from pydantic import BaseModel as PydanticBaseModel

class SectionSchema(PydanticBaseModel):
    title: str
    content: str
    index: int

class SupplementaryPromptSchema(PydanticBaseModel):
    style: str
    prompt: str


class TopicSchema(PydanticBaseModel):
    title: str
    description: str
    duration: int
    sections: list[SectionSchema]
    supplementary_prompts: list[SupplementaryPromptSchema]
    is_recommended: bool
