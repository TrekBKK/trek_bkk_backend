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
    start_id: str | None = None,
    end_id: str | None = None,
    n_stops: int = 3,
    d_p2p: int = 1000,
    tags: Annotated[list[str], Query()] = ['restaurant', 'cafe', 'art_gallery'],
    is_test: bool = False
):
    coord_list = generator_service.recommend_places(
        start_id=start_id,
        end_id=end_id,
        n_stops=n_stops, d_p2p=d_p2p,
        tags=tags,
        is_test=is_test
    )
    return coord_list
