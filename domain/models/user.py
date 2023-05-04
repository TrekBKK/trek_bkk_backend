from pydantic import Field
from typing import List, Dict, Union
from domain.models.objectId import BaseModel, ObjectId


class User(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    name: str | None = None
    email: str | None = None
    photo: str | None = None
    favorite_route: list | None = None
    history_route: list | None = None
    preference: Dict[str, Union[str, List[str]]] | None = None

    class Config:
        arbitrary_types_allowed = True
