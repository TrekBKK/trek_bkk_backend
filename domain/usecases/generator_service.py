import json
import math
import os
from pymongo import MongoClient
from adapters import TrekBKKRecommender
from shapely.geometry import Point
import pandas as pd
import geopandas as gpd
from geopy import distance

from dotenv import load_dotenv
import googlemaps

from domain.models.place import Place


def midpoint(
        start_lat: float, start_lng: float,
        end_lat: float, end_lng: float
):
    lat1 = math.radians(start_lat)
    lon1 = math.radians(start_lng)
    lat2 = math.radians(end_lat)
    lon2 = math.radians(end_lng)

    bx = math.cos(lat2) * math.cos(lon2 - lon1)
    by = math.cos(lat2) * math.sin(lon2 - lon1)
    lat3 = math.atan2(math.sin(lat1) + math.sin(lat2), \
           math.sqrt((math.cos(lat1) + bx) * (math.cos(lat1) \
           + bx) + by**2))
    lon3 = lon1 + math.atan2(by, math.cos(lat1) + bx)

    return [round(math.degrees(lat3), 7), round(math.degrees(lon3), 7)]

def search_nerby(lat:float, lng:float, radius:int, place_types:list[str]):
    results = []
    load_dotenv()
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    gmaps = googlemaps.Client(GOOGLE_API_KEY)

    # for each tag, get 2 pages of the results
    for p_type in place_types:
        resp = gmaps.places_nearby(
            location=[lat, lng],
            radius=radius,
            type=p_type
        )
        results.extend(resp['results'])
        # call each tag twice
        if resp['next_page_token']:
            resp = gmaps.places_nearby(page_token=resp['next_page_token'])
            results.extend(resp['results'])

    return results

def extract_field(results: list[dict]):
    places_list = []
    for r in results:
        temp_p = Place(
            place_id=r['place_id'],
            name=r['name'],
            icon=r['icon'],
            latitude=r['geometry']['location']['lat'],
            longitude=r['geometry']['location']['lng'],
            rating=r.get('rating', 0),
            types=r['types']
        )
        places_list.append(temp_p)
    return places_list

def get_places_between(
        start_lat: float, start_lng: float,
        end_lat: float, end_lng: float,
        tags: list[str]
):
    # get coord from place_id
    
    # calculate coord between start and and end
    [mid_lat, mid_lng] = midpoint(start_lat, start_lng, end_lat, end_lng)
    # get radius for searching nearby places
    mid_dis = math.floor(distance.distance((mid_lat, mid_lng), (end_lat, end_lng)).meters)    
    # send coord and tags to Nearby Search service by GoogleMap API
    returned_places = search_nerby(mid_lat, mid_lng, mid_dis, tags)
    # extract lat, lng, rating from response
    extracted_places = extract_field(returned_places)
    # return list of GoogleMap's Place object
    return extracted_places

def get_test_data():
    raw_places = {}

    with open('static/testing_places_data.json') as places_json:
        raw_places = json.load(places_json)
    
    return extract_field(raw_places['places'])

def get_place_from_id(place_id: str):
    load_dotenv()
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    gmaps = googlemaps.Client(GOOGLE_API_KEY)

    res = gmaps.place(place_id=place_id)['result']
    return Place(
            place_id=res['place_id'],
            name=res['name'],
            icon=res['icon'],
            latitude=res['geometry']['location']['lat'],
            longitude=res['geometry']['location']['lng'],
            rating=res['rating'],
            types=res['types']
        )


def data_to_gdf(places: Place):
    idx = []
    lat = []
    lon = []
    rating = []

    for i, place in enumerate(places):
        idx.append(i)
        lat.append(place.latitude)
        lon.append(place.longitude)
        rating.append(place.rating)

    gdf = gpd.GeoDataFrame(
        {
            'Index': idx,
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


def get_unique_index(index_lists: list[int]):
    idx = []
    for lst in index_lists:
        for i in lst.values.tolist():
            idx.append(i)
    return list(set(idx))

# input format:
# place_id src
# place id dest
# stops
# tags
# return format: [(lat_1, lon_1), (lat_2, lon_2)]
def recommend_places(
        n_stops: int,        
        tags: list[str],
        is_test: bool,
        start_id: str | None = None,
        end_id: str | None = None,
        d_p2p: int = 2000,
):

    if is_test:
        # set start and end place instance for testing purpose
        start_place = Place(
            place_id="ChIJWaoiBdmY4jAReVIX1maq_-I",
            icon="https://maps.gstatic.com/mapfiles/place_api/icons/v1/png_71/worship_dharma-71.png",
            latitude=13.7377075,
            longitude=100.5134545,
            name="Wat Traimit Withayaram Worawihan",
            rating=4.6,
            types=[
                "tourist_attraction",
                "place_of_worship",
                "point_of_interest",
                "establishment"
            ]
        )
        end_place = Place(
            place_id="ChIJZ-IlRCKZ4jARzgWVA3vA_0k",
            icon="https://maps.gstatic.com/mapfiles/place_api/icons/v1/png_71/worship_dharma-71.png",
            latitude=13.7429042,
            longitude=100.5092772,
            name="Wat Traimit Withayaram Worawihan",
            rating=4.5,
            types=[
                "tourist_attraction",
                "place_of_worship",
                "point_of_interest",
                "establishment"
            ]
        )
        filtered_places = get_test_data()
        d_p2p = 2000
        n_stops = 3
    else:
        start_place = get_place_from_id(start_id)
        end_place = get_place_from_id(end_id)
        # search for places that are between start and end point
        filtered_places = get_places_between(
            start_place.latitude, start_place.longitude,
            end_place.latitude, end_place.longitude,
            tags
        )

    gdf = data_to_gdf(filtered_places)
    start_point = Point(start_place.longitude, start_place.latitude)
    end_point = Point(end_place.longitude, end_place.latitude)
    recommender = TrekBKKRecommender(
        start_point, end_point,
        d_p2p, n_stops
    )
    recommender.set_gdf(gdf)

    selected_idx, stops_list = recommender.recommend()
    stops_idx = get_unique_index(stops_list)
    poi_in_route_gdf = recommender.get_gdf().iloc[selected_idx].copy()
    poi_optional_gdf = recommender.get_gdf().iloc[stops_idx].copy()
    
    # poi_in_route = poi_in_route_gdf.loc[:, 'Index']
    # poi_optional = poi_optional_gdf.loc[:, 'Index']
    poi_in_route = poi_in_route_gdf.loc[:,
                                        'geometry'].apply(lambda x: x.coords[0])
    # number of optional places = n_stop * 2
    poi_optional = poi_optional_gdf.loc[:,
                                        'geometry'].apply(lambda x: x.coords[0])
    
    return {'recommended': poi_in_route.tolist(), 'optional': poi_optional.tolist()}
