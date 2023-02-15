from fastapi import APIRouter

from domain.models import User
from domain.usecases import user_service

router = APIRouter(prefix="/user")


@router.get("/")
async def get_users():
    user_service.get_users()
    return "asd"


@router.post("/")
async def temp(user: User):
    print("in post request")
    print(user)
    return
