from datetime import datetime
import json
from math import atan2, cos, radians, sin, sqrt
import os
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import HTTPException
from pymongo import MongoClient
import requests
from domain.models.place import Place
from domain.models.user import User
import pandas as pd
from pytz import timezone

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

def get_item_by_id(_id:str, col_name:str, client: MongoClient):
    # query data using id
    db = client["trekDB"]
    collection = db[col_name]

    try:
        _item = collection.find_one({"_id": ObjectId(_id)})
        if _item:
            return _item
        raise HTTPException(status_code=404, detail=f"{col_name} not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def get_place_related_detail(place_id: str):
    # wanted data: district, rating, types
    place_detail = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json",
        params={"fields": "address_components,name,rating,types", 
                "place_id": place_id, 
                "key": API_KEY},
    ).json()["result"]
    address = place_detail["address_components"]
    district = ""
    for component in address:
        district = component["long_name"]
        if "Khet" in district:
            break
    place_obj = Place(
        place_id=place_id, 
        name=place_detail.get("name", 'NA'),
        rating=place_detail.get("rating", 0.5), 
        types=place_detail["types"], 
        district=district
    )
    return place_obj

def transform_timestamp(timestamp: str = None, use_current: bool = False):
    # check if datetime a daytime & weekend
    # check current datetime
    if use_current:
        dt_obj = datetime.now(timezone("Asia/Bangkok"))
    # check from input
    else:
        dt_obj = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %z")
    is_daytime = dt_obj.time().hour in range(6, 18)
    is_weekend = dt_obj.isoweekday() > 5
    return [int(is_daytime), int(is_weekend)]

def prepare_input(
        user_pref: User, 
        place_feat: list[list[Place]],
        hist_ctxt: list[dict[int, int]], 
        for_train: bool = True):
    df = pd.DataFrame(columns=[
        "pref_type", "pref_dist", "pref_stop",
        "place_id", "place_type", "district", "rating",
        "daytime", "weekend"
    ])
    for i, places in enumerate(place_feat):
        for place in places:
            feat_dict = {
                "pref_type": [user_pref.preference["type"]], 
                "pref_dist": [user_pref.preference["distance"]], 
                "pref_stop": [user_pref.preference["stop"]],
                "place_id": [place.place_id], 
                "place_type": [place.types], 
                "district": [place.district], 
                "rating": [place.rating],
                "daytime": [hist_ctxt[i][0]], 
                "weekend": [hist_ctxt[i][1]]
            }
            df = pd.concat([df, pd.DataFrame(feat_dict)], ignore_index=True)

    # create dummy variable for place type
    with open('static/place_types.json') as types_json:
        types_list = json.load(types_json)["types"]
    for t in types_list:
        is_place_tag = df["place_type"].apply(lambda tags: int(t in tags)).rename(t)
        is_pref_tag = df["pref_type"].apply(lambda tags: 10 * int(t in tags)).rename(t)
        df[t] = is_place_tag.add(is_pref_tag)
    df = df.drop(columns=["place_type", "pref_type"])

    # create dummy variable for district
    with open('static/bangkok_districts.json') as types_json:
        districts_list = json.load(types_json)["districts"]
    for district in districts_list:
        is_district = df["district"].apply(lambda d: int(d == district)).rename(district)
        df[district] = is_district
    df = df.drop(columns=["district"])
    
    if for_train:
        df = df.groupby(by=df.columns.tolist(), axis=0, as_index=False).size()
        df = df.rename(columns={"size": "y"})

    return df

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using the Spherical Law of Cosines.
    """
    R = 6373.0  # radius of the Earth in km

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance

def search_nearby_places(src_id: str, dest_id: str, stops: int, tags: list[str]):
    src = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json",
        params={"fields": "geometry", "place_id": src_id, "key": API_KEY},
    ).json()["result"]["geometry"]["location"]

    dest = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json",
        params={"fields": "geometry", "place_id": dest_id, "key": API_KEY},
    ).json()["result"]["geometry"]["location"]

    # calculate the middle point between start and end points in degrees
    mid_lat = (src["lat"] + dest["lat"]) / 2
    mid_lng = (src["lng"] + dest["lng"]) / 2

    # calculate the distance between the middle point and each of the start and end points
    d_start = calculate_distance(src["lat"], src["lng"], mid_lat, mid_lng)
    d_end = calculate_distance(dest["lat"], dest["lng"], mid_lat, mid_lng)

    # choose the maximum distance as the radius
    radius = max(d_start, d_end)

    # Convert to meter &
    # multiply by radius factor to extend the coverage beyond starting and ending points
    radius = radius * 1000 * 1.1

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    payload = {
        "location": f"{str(mid_lat)},{str(mid_lng)}",
        "radius": radius,
        "key": API_KEY,
    }

    raw = []
    res = requests.Response()

    if tags:
        for tag in tags:
            payload["type"] = tag

            res = requests.get(
                url,
                params=payload,
            )

            raw = raw + res.json()["results"]

    else:
        res = requests.get(
            url,
            params=payload,
        )

        raw = res.json()["results"]

    while len(raw) < 60 and res.json().get("next_page_token"):
        res = requests.get(
            url,
            params={"key": API_KEY, "pagetoken": res.json()["next_page_token"]},
        )

        raw = raw + res.json()["results"]

    unique_places = {}

    for place in raw:
        if place["place_id"] not in unique_places.keys():
            idx = place["vicinity"].find('Khet')
            place_obj = Place(
                place_id=place["place_id"], 
                name=place.get("name", "NA"),
                rating=place.get("rating", 0.5), 
                types=place["types"], 
                district=(place["vicinity"][idx:] if idx > -1 else "")
            )
            unique_places[place["place_id"]] = place_obj

    places = list(unique_places.values())
    # reshape list to a 2D list
    # to make the list compatible with the prepare input function
    return [[p] for p in places]

def recommend_places(
        src_id: str, dest_id: str, stops: int, tags: list[str], 
        user_id: str, client: MongoClient
    ):
    #### prepare data for training ####
    user_data = get_item_by_id(_id=user_id, col_name="user", client=client)
    # data for user profile
    user_obj = User(_id=user_id, preference=user_data["preference"])    
    # extract places and context from the route history
    history_list = user_data["history_route"]
    waypoint_in_route = []
    hist_context = []
    for hist in history_list:
        route_data = get_item_by_id(_id=hist["route_id"], col_name="routes", client=client)
        waypoint_list = route_data["geocoded_waypoints"]
        waypoint_in_route.append(waypoint_list)
        ctxt = transform_timestamp(timestamp=hist["timestamp"])
        hist_context.append(ctxt)
    # get place's feature
    unique_places = {}
    places_list = []
    for waypoint_list in waypoint_in_route:
        places = []
        for i, waypoint in enumerate(waypoint_list):
            if i > 0:
                break
            place_id = waypoint["place_id"]
            place = unique_places.get(place_id)
            if not place:
                place = get_place_related_detail(place_id=place_id)
                unique_places[place_id] = place
            places.append(place)
        places_list.append(places)
    # df for training the model
    train_df = prepare_input(
        user_pref=user_obj, 
        place_feat=places_list, 
        hist_ctxt=hist_context
    )
    #### prepare data for recommendation ####
    candidate_places = search_nearby_places(src_id=src_id, dest_id=dest_id, stops=stops, tags=tags)
    # get current datetime and check for daytime & weekend
    # to create context
    current_dt_check = transform_timestamp(use_current=True)
    current_ctxt = [current_dt_check for _ in range(len(candidate_places))]
    # df for places to recommend to user
    pred_df = prepare_input(
        user_pref=user_obj, 
        place_feat=candidate_places, 
        hist_ctxt=current_ctxt,
        for_train=False
    )

    return {"msg": "success so far"}