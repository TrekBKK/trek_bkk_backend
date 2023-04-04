from pydantic import BaseModel

class Place(BaseModel):
    place_id: str
    name: str
    icon: str
    latitude: float
    longitude: float
    rating: float
    types: list[str]