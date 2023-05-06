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
)


router = APIRouter(prefix="/routes")


@router.get("")
def findAllByKey(searchKey: str, client: MongoClient = Depends(get_mongo_client)):
    res = search_service.find_all_by_key(searchKey, client)
    print(res)
    return res


@router.get("/place")
def findAllByPlace(
    src_id: str | None = None,
    dest_id: str | None = None,
    place_ids: list[str] | None = Query(default=None),
    client: MongoClient = Depends(get_mongo_client),
):
    res = search_service.find_all_by_places(src_id, dest_id, place_ids, client)
    return res


@router.get("/generate")
def generate_route(
    src_id: str,
    dest_id: str,
    stops: int,
    tags: list[str] = Query(default=[]),
    useAlgorithm: bool = False,
):
    if useAlgorithm:
        return
    else:
        res = rating_recommendation_service.nearby_search(
            src_id=src_id, dest_id=dest_id, stops=stops, tags=tags
        )
        return res


@router.get("/propose")
def find_proposed_routes():
    return "healthy"


@router.post("/propose")
def propose_route(data: ProposeInput, client: MongoClient = Depends(get_mongo_client)):
    res = propose_service.propose(data, client)
    return responses.JSONResponse(content=res)
