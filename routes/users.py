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


@router.post("/image")
async def update_image(request: Request, client: MongoClient = Depends(get_mongo_client)):
    data = await request.json()
    a = user_service.update_image(data, client)
    return responses.JSONResponse(content=a)


@router.get("/favorite")
def getFavoriteRoutes(user_id: str, client: MongoClient = Depends(get_mongo_client)):
    a = user_service.get_favorite_routes(user_id, client)

    return responses.JSONResponse(content=a)


@router.patch("/favorite")
async def updateRoute(request: Request, client: MongoClient = Depends(get_mongo_client)):
    data = await request.json()
    user_id = data["user_id"]
    route_id = data["route_id"]
    a = user_service.update_favorite_routes(user_id, route_id, client)
    return responses.JSONResponse(content=a)


@router.get("/history")
def getHistoryRoutes(user_id: str, client: MongoClient = Depends(get_mongo_client)):
    a = user_service.get_history_routes(user_id, client)

    return responses.JSONResponse(content=a)


@router.patch("/history")
async def getHistoryRoutes(request: Request, client: MongoClient = Depends(get_mongo_client)):
    data = await request.json()
    user = {"user_id": data["user_id"], "route": {
        "route_id": data["route_id"], "timestamp": data["timestamp"]}}
    a = user_service.update_history_routes(user, client)

    return responses.JSONResponse(content=a)


@router.patch("/pref")
def updateUserPref(user: User, client: MongoClient = Depends(get_mongo_client)):
    a = user_service.update_user_pref(user, client)

    return responses.JSONResponse(content=a)
