from pydantic import BaseModel as PydanticBaseModel

class ChoiceSchema(PydanticBaseModel):
    letter: str  # e.g., "A", "B", "C", "D"
    text: str

class QuestionSchema(PydanticBaseModel):
    question_text: str
    choices: list[ChoiceSchema]
    correct_answer_letter: str  # e.g., "A"

class QuizSchema(PydanticBaseModel):
    questions: list[QuestionSchema]

class SectionSchema(PydanticBaseModel):
    title: str
    content: str
    index: int
    quiz: QuizSchema

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
    quiz: QuizSchema