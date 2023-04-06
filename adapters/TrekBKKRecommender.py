import pandas as pd
import geopandas as gpd
import pyproj
from shapely import Point
from geopy import distance

class TrekBKKRecommender:
    def __init__(
            self, 
            start_point: Point, end_point: Point, 
            d_p2p: int, n_stops: int) -> None:
        self.start_point = start_point
        self.end_point = end_point
        self.d_p2p = d_p2p
        self.n_stops = n_stops
        self.gdf = None

    def set_gdf(self, gdf: gpd.GeoDataFrame):
        self.gdf = gdf

    def get_gdf(self):
        return self.gdf

    def get_mock_data(self):
        poi_df = pd.read_csv('static/mock_data/Mock_filtered_POIs.csv')
        self.gdf = gpd.GeoDataFrame(
            poi_df,
            geometry=gpd.points_from_xy(
                poi_df['Longitude'],
                poi_df['Latitude']
            ),
            crs=4326
        )

    def data_to_gdf(self, 
                    POI_id: str, 
                    lat: float, lon: float, 
                    rating: int, 
                    n_visits: int | None = None):
        gdf = gpd.GeoDataFrame(
            {
                'POI_id': POI_id,
                'Rating': rating,
                'Visit Count': n_visits 
            },
            geometry=gpd.points_from_xy(
                lon,
                lat
            ),
            crs=4326
        )
        return gdf
    
    def print_detail(self):
        print('---------Recommender Detail----------')
        print(f'start point:\t{self.start_point.coords[0]}')
        print(f'end point:\t{self.end_point.coords[0]}')
        print(f'number of stops:\t{self.n_stops}')
        print()
        print('======== first 5 record of filtered places ========')
        print(self.gdf.head())

    def recommend(self):
        stops_idx = []
        selected_idx = []
        interested_point = self.start_point
        end_point = self.end_point
        distance_p2p = self.d_p2p
        geodesic = pyproj.Geod(ellps='WGS84')
        is_end_within = False

        gdf_3857 = self.gdf.to_crs(3857)

        # convert end_point from epsg:4326 to 3857
        # for distance-related operation
        s_end = gpd.GeoSeries(
            [end_point],
            crs=4326
        )
        s_end = s_end.to_crs(3857)
        end_point_3857 = s_end[0]

        while not is_end_within:
            # calculate bearing
            bearing_goal, back_azimuth, distance_to_goal = geodesic.inv(
            interested_point.x, interested_point.y,
            end_point.x, end_point.y
            )
            # find lat/long from the given distance, lat/long, bearing
            search_lat, search_long, search_alt = distance.distance(meters=distance_p2p/2).destination(
                (interested_point.y, interested_point.x), 
                bearing=bearing_goal)
            # convert CRS to 3857 for distance-related operation
            s_itm = gpd.GeoSeries(
                [Point(search_long, search_lat)],
                crs=4326
            )
            s_itm = s_itm.to_crs(3857)
            f = s_itm.buffer(distance_p2p/2).unary_union
            # check if end point is within search area
            is_end_within = end_point_3857.within(f)
            if not is_end_within:
                # filter places that are within search area
                mask = gdf_3857['geometry'].intersection(f)
                in_radius_gdf = self.gdf[~mask.is_empty]
                # if there are no places in search area, set its center as interested point
                if in_radius_gdf.empty:
                    interested_point = Point(search_long, search_lat)
                else:
                    in_radius_gdf = in_radius_gdf.sort_values(by='Rating', ascending=False)
                    stops_idx.append(in_radius_gdf.index)
                    # select the highest rating place
                    selected_idx.append(in_radius_gdf.index[0])
                    # set next interested point
                    interested_point = in_radius_gdf.head(1)['geometry'].to_crs(4326).values[0]
            
        return selected_idx, stops_idx