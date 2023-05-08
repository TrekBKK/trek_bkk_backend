from pydantic import BaseModel

class Place(BaseModel):
    place_id: str
    name: str | None = None
    icon: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    rating: float | None = None
    types: list[str] | None = None
    district: str | None = None