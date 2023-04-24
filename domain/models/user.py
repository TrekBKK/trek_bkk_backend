from pydantic import Field

from domain.models.objectId import BaseModel, ObjectId


class User(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    name: str
    email: str
    perference: dict | None = None
    favorite_route: list | None = None
    places_history: dict | None = None

    class Config:
        arbitrary_types_allowed = True
