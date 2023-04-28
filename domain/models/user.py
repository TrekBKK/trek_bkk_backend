from pydantic import Field

from domain.models.objectId import BaseModel, ObjectId


class User(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    name: str
    email: str
    photo: str | None = None
    favorite_route: list | None = None
    places_history: list | None = None
    perference: bool | None = None

    class Config:
        arbitrary_types_allowed = True
