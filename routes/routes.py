from fastapi import APIRouter, Depends, Query, responses, Request
from pymongo import MongoClient

from adapters.mongodb import get_mongo_client
from domain.models.propose import ProposeInput
from domain.usecases import (
    generator_service,
    home_service,
    route_service,
    search_service,
    rating_recommendation_service,
    propose_service,
    route_generator_service,
)


router = APIRouter(prefix="/routes")


@router.get("")
def find_all_by_key(searchKey: str, client: MongoClient = Depends(get_mongo_client)):
    res = search_service.find_all_by_key(searchKey, client)
    return res


@router.get("/home")
def routes_for_home_page(client: MongoClient = Depends(get_mongo_client)):
    res = home_service.get_routes_for_home(client)
    return responses.JSONResponse(content=res)


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
    use_algorithm: bool = False,
    user_id: str = "",
    client: MongoClient = Depends(get_mongo_client),
):
    if use_algorithm and user_id is not "":
        # res = route_generator_service.recommend_places_old(
        #     src_id=src_id,
        #     dest_id=dest_id,
        #     stops=stops,
        #     tags=tags,
        #     user_id=user_id,
        #     client=client,
        # )
        res = route_generator_service.recommend_places_new(
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


@router.post("/edited")
async def edited_route(
    request: Request, client: MongoClient = Depends(get_mongo_client)
):
    data = await request.json()
    res = route_service.edited(data, client)
    return responses.JSONResponse(content=res)
