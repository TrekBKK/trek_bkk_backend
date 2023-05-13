from pydantic import BaseModel


class ProposeInput(BaseModel):
    user_id: str
    name: str
    description: str
    distance: float
    stops: int
    waypoints: list
    polyline: str
    imagePath: str
