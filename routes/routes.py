from fastapi import APIRouter, Depends, Query, responses, Request
from pydantic import BaseModel
from pymongo import MongoClient

from adapters.mongodb import get_mongo_client
from domain.models.propose import ProposeInput
from domain.usecases import (
    generator_service,
    search_service,
    rating_recommendation_service,
    propose_service,
    route_generator_service,
)


router = APIRouter(prefix="/routes")


@router.get("")
def find_all_by_key(searchKey: str, client: MongoClient = Depends(get_mongo_client)):
    res = search_service.find_all_by_key(searchKey, client)
    print(res)
    return res


@router.get("/place")
def find_all_by_place(
    src_id: str | None = None,
    dest_id: str | None = None,
    place_ids: list[str] | None = Query(default=None),
    client: MongoClient = Depends(get_mongo_client),
):
    res = search_service.find_all_by_places(src_id, dest_id, place_ids, client)
    return res


@router.get("/types")
def get_all_types(client: MongoClient = Depends(get_mongo_client)):
    res = search_service.get_all_types(client)
    return res


@router.get("/generate")
def generate_route(
    src_id: str,
    dest_id: str,
    stops: int,
    tags: list[str] = Query(default=[]),
    useAlgorithm: bool = False,
    user_id: str | None = None,
    client: MongoClient = Depends(get_mongo_client),
):
    if useAlgorithm and user_id is not None:
        res = route_generator_service.recommend_places(
            src_id=src_id,
            dest_id=dest_id,
            stops=stops,
            tags=tags,
            user_id=user_id,
            client=client,
        )
        return res
    else:
        res = rating_recommendation_service.nearby_search(
            src_id=src_id, dest_id=dest_id, stops=stops, tags=tags
        )
        return res


@router.get("/propose")
def find_proposed_routes(user_id: str, client: MongoClient = Depends(get_mongo_client)):
    res = propose_service.find_all_by_user_id(user_id, client)
    return responses.JSONResponse(content=res)


@router.post("/propose")
def propose_route(data: ProposeInput, client: MongoClient = Depends(get_mongo_client)):
    res = propose_service.propose(data, client)
    return responses.JSONResponse(content=res)
