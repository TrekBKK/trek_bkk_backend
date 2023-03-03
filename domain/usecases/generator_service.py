from pymongo import MongoClient
from adapters import TrekBKKRecommender
from shapely.geometry import Point
import pandas as pd
import geopandas as gpd

def get_places_between(
        start_lat: float, start_lng: float,
        end_lat: float, end_lng: float, 
        tags: list[str]
):
    # calculate coord between start and and end
    # send coord and tags to Nearby Search service by GoogleMap API
    # extract lat, lng, rating from response
    # return list of GoogleMap's Place object
    pass

def data_to_gdf(places):
    POI_id = []
    lat = []
    lon = []
    rating = []

    for place in places:
        POI_id.append(str(place.id))
        lat.append(place.latitude)
        lon.append(place.longitude)
        rating.append(place.rating)

    gdf = gpd.GeoDataFrame(
        {
            'POI_id': POI_id,
            'Rating': rating, 
            'Latitude': lat,
            'Longitude': lon
        },
        geometry=gpd.points_from_xy(
            lon,
            lat
        ),
        crs=4326
    )    
    return gdf

def get_unique_index(index_lists):
    idx = []
    for lst in index_lists:
        for i in lst.values.tolist():
            idx.append(i)
    return list(set(idx))

# return format: [(lat_1, lon_1), (lat_2, lon_2)]
def recommend_places(
        start_lat: float, start_lng: float,
        end_lat: float, end_lng: float, 
        n_stops: int,
        d_p2p: int,        
        tags: list[str],
        is_test: bool
):   

    if is_test:
        # set start and end coords for testing purpose
        start_point = Point(100.60457977018594, 13.920575400368827)
        end_point = Point(100.56451592224371, 13.813597590137617)
        d_p2p = 2000
        n_stops = 3
        recommender = TrekBKKRecommender(
            start_point, end_point,
            d_p2p, n_stops
        )
        recommender.get_mock_data()
    else:        
        # search for places that are between start an end point
        filtered_places = get_places_between(
            start_lat, start_lng,
            end_lat, end_lng, 
            tags
        )
        gdf = data_to_gdf(filtered_places)
        start_point = Point(start_lng, start_lat)
        end_point = Point(end_lng, end_lat)
        recommender = TrekBKKRecommender(
            start_point, end_point,
            d_p2p, n_stops
        )
        recommender.set_gdf(gdf)
    
    selected_idx, stops_list = recommender.recommend()
    stops_idx = get_unique_index(stops_list)
    poi_in_route_gdf = recommender.get_gdf().iloc[selected_idx].copy()
    poi_optional_gdf = recommender.get_gdf().iloc[stops_idx].copy()
    poi_in_route = poi_in_route_gdf.loc[:, 'geometry'].apply(lambda x: x.coords[0])
    poi_optional = poi_optional_gdf.loc[:, 'geometry'].apply(lambda x: x.coords[0])

    return {'recommended': poi_in_route.tolist(), 'optional': poi_optional.tolist()}