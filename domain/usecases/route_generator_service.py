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
import numpy as np
from pytz import timezone
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

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
        params={"fields": "address_components,name,rating,types,geometry", 
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
        district=district,
        latitude=place_detail["geometry"]["location"]["lat"],
        longitude=place_detail["geometry"]["location"]["lng"]
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
        df = pd.concat([df, is_place_tag.add(is_pref_tag)], axis=1)
    df = df.drop(columns=["place_type", "pref_type"])

    # create dummy variable for district
    with open('static/bangkok_districts.json') as types_json:
        districts_list = json.load(types_json)["districts"]
    for district in districts_list:
        is_district = df["district"].apply(lambda d: int(d == district)).rename(district)
        df = pd.concat([df, is_district], axis=1)
    df = df.drop(columns=["district"])

    if for_train:
        modified_df = df.copy()
        modified_df = modified_df.groupby(by=modified_df.columns.tolist(), axis=0, as_index=False).size()
        modified_df = modified_df.rename(columns={"size": "y"})
        df = modified_df

    return df

def map_id(
        id_list: list[str] | list[list[str]],
        target_id_list: list[list[str]]
    ):
    # flatten the list
    flat_list = []
    for lst in id_list:
        flat_list.extend(lst)
    id_array = np.array(flat_list)
    id_array = np.unique(id_array)
    # map index to id in dataframe
    mapped_id_list = []
    for lst in target_id_list:
        mapped_id = []
        for pid in lst:
            idx = np.where(id_array == pid)[0][0]
            mapped_id.append(idx)
        mapped_id_list.append(mapped_id)
    return (id_array, mapped_id_list)

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
        # ! don't forget to remove break in final ver.
        for i, tag in enumerate(tags):
            if i > 0:
                break
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

    # ! don't forget to un-comment in final ver.
    # while len(raw) < 60 and res.json().get("next_page_token"):
    #     res = requests.get(
    #         url,
    #         params={"key": API_KEY, "pagetoken": res.json()["next_page_token"]},
    #     )

    #     raw = raw + res.json()["results"]

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

def prepare_response(
        candidate_places: list[list[Place]],
        recommended_idx: list[int]
    ):
    rec_list = []
    i = 0
    while (i < 20) and (i < len(recommended_idx)):
        recommended_place = candidate_places[recommended_idx[i]][0]
        place_dict = {
            "place_id": recommended_place.place_id,
            "name": recommended_place.name,
            "geometry": {
                "location": {
                    "lat": recommended_place.latitude,
                    "lng": recommended_place.longitude
                }
            }
        }
        rec_list.append(place_dict)
    return rec_list

def recommend_places(
        src_id: str, dest_id: str, stops: int, tags: list[str], 
        user_id: str, client: MongoClient
    ):
    #* #### prepare data for training ####
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
            # ! don't forget to remove break in final ver.
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

    #* #### prepare data for recommendation ####
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

    train_place_id = list(unique_places.keys())
    # flatten the list then get the place_id
    pred_place_id = [p.place_id for lst in candidate_places for p in lst]
    #* map place_id in train and pred dataframe
    id_array, mapped_id_list = map_id(
        [train_place_id, pred_place_id],
        [train_df["place_id"].tolist(), pred_df["place_id"].tolist()]
    )
    train_df["place_id"] = mapped_id_list[0]
    pred_df["place_id"] = mapped_id_list[1]

    #* #### train model ####
    X = train_df.loc[:, train_df.columns != 'y'].values
    y = train_df.loc[:, 'y'].values
    y = y.reshape(-1, 1)
    sc_y = StandardScaler()
    y = sc_y.fit_transform(y)
    y = y.reshape(-1)

    regressor = SVR(kernel = 'rbf')
    regressor.fit(X, y)

    #* #### recommend places ####
    X_pred = pred_df.loc[:, :].values
    y_pred = regressor.predict(X_pred)
    y_pred = sc_y.inverse_transform(y_pred.reshape(-1, 1)).reshape(-1)
    pred_df = pd.concat([pred_df, pd.Series(y_pred, name='y_pred')], axis=1)
    recommended_idx = pred_df.sort_values(by=['y_pred']).index.values.tolist()
    recommended_places = prepare_response(candidate_places, recommended_idx)

    return recommended_places