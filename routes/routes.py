from fastapi import APIRouter, Depends, Query
from pymongo import MongoClient
from typing import Annotated

from adapters.mongodb import get_mongo_client
from domain.usecases import generator_service, search_service


router = APIRouter(prefix='/routes')


@router.get('')
def findAllByKey(searchKey: str, client: MongoClient = Depends(get_mongo_client)):
    res = search_service.find_all_by_key(searchKey, client)
    return res


@router.get('/place')
def findAllByPlace(src_id: str | None = None, dest_id: str | None = None, place_ids: list[str] | None = Query(default=None), client: MongoClient = Depends(get_mongo_client)):
    res = search_service.find_all_by_places(src_id, dest_id, place_ids, client)
    return res


@router.get('/generate')
def generate_route(
    start_lat: float = 0, start_lng: float = 0,
    end_lat: float = 1, end_lng: float = 1,
    n_stops: int = 3,
    d_p2p: int = 2,
    tags: list[str] = ['0', '1', '2'],
    is_test: bool = False
):
    coord_list = generator_service.recommend_places(
        start_lat, start_lng,
        end_lat, end_lng,
        n_stops, d_p2p,
        tags,
        is_test
    )
    return coord_list
