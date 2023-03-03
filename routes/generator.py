from fastapi import APIRouter

from domain.usecases import generator_service


router = APIRouter(prefix='/generate')

@router.get('/')
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