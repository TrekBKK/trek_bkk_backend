from fastapi import APIRouter, Depends, responses, Request

from pymongo import MongoClient

from adapters import get_mongo_client

from domain.models import User
from domain.usecases import user_service

router = APIRouter(prefix="/user")


@router.get("/")
async def get_users():
    return "asd"


@router.post("/")
def getUser(user: User, client: MongoClient = Depends(get_mongo_client)):
    a = user_service.get_user(user, client)
    a["_id"] = str(a["_id"])
    return responses.JSONResponse(content=a)


@router.post("/favorite")
def getFavoriteRoutes(user: User, client: MongoClient = Depends(get_mongo_client)):
    a = user_service.get_favorite_routes(user, client)

    return responses.JSONResponse(content=a)


@router.patch("/favorite")
async def updateRoute(request: Request, client: MongoClient = Depends(get_mongo_client)):
    data = await request.json()
    user_id = data["user_id"]
    route_id = data["route_id"]
    a = user_service.update_favorite_routes(user_id, route_id, client)
    return responses.JSONResponse(content=a)


@router.post("/history")
def getHistoryRoutes(user: User, client: MongoClient = Depends(get_mongo_client)):
    a = user_service.get_history_routes(user, client)

    return responses.JSONResponse(content=a)


@router.patch("/pref")
def updateUserPref(user: User, client: MongoClient = Depends(get_mongo_client)):
    a = user_service.update_user_pref(user, client)

    return responses.JSONResponse(content=a)
