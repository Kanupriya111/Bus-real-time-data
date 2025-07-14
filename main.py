import requests  # For accessing websites
from google.transit import gtfs_realtime_pb2 #Importing GTFS-realtime data feed from a particular URL
from datetime import datetime, timedelta # To convert string into datetime format
import pytz # allows accurate and cross platform timezone calculations.
import pandas as pd  # For dataframes
import os # For OS related functions
import time  # For system time
import csv # For reading and writing CSV
import math  #to perform the caculations of Haversine function

# # GTFS real-time vehicle positions URL
pb_url = 'xxx'

# Setup paths
loc = os.path.dirname(os.path.realpath(__file__))
routes = pd.read_csv(os.path.join(loc, "routes.txt"))
stops = pd.read_csv(os.path.join(loc, "stops.txt")).astype({'stop_lat': float, 'stop_lon': float})
stop_times = pd.read_csv(os.path.join(loc, "stop_times.txt"))
trips = pd.read_csv(os.path.join(loc, "trips.txt"))

# Merge GTFS files
stop_times = stop_times.merge(trips[['trip_id', 'route_id']], on='trip_id')
stop_times = stop_times.merge(routes[['route_id', 'route_long_name']], on='route_id')
stop_times['stop_sequence'] = stop_times['stop_sequence'].astype(int)

# Time setup
ist = pytz.timezone("Asia/Kolkata")
end_time = datetime.now(ist) + timedelta(hours=2)

# Target filter
target_route_id = 720
target_route_name = "706DOWN"
target_trip_id = "720_11_16"

# Output CSV setup
output_path = os.path.join(loc, "filtered_new.csv")
fieldnames = ['vehicle_id', 'route_id', 'route_name', 'trip_id',
              'stop_id', 'stop_name', 'stop_sequence',
              'stop_lat', 'stop_lon', 'arrival_date', 'arrival_time', 'txt_arrival_time']

if not os.path.isfile(output_path):
    with open(output_path, 'w', newline='') as f:
        csv.DictWriter(f, fieldnames=fieldnames).writeheader()

# Haversine function (meters)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Memory
vehicle_state = {}  # key: vehicle_id → dict with keys: prev_lat, prev_lon, remaining_stops, last_stop_seq

print(f"Logging started until {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

while datetime.now(ist) < end_time:
    try:
        feed = gtfs_realtime_pb2.FeedMessage()
        resp = requests.get(pb_url)
        feed.ParseFromString(resp.content)
    except Exception as e:
        print("Error fetching data:", e)
        time.sleep(10)
        continue

    now = datetime.now(ist)

    with open(output_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        for entity in feed.entity:
            v = entity.vehicle
            vehicle_id = v.vehicle.id
            route_id = int(float(v.trip.route_id))
            trip_id = v.trip.trip_id
            
            if route_id != target_route_id or trip_id != target_trip_id:
                continue
            route_name = routes.loc[routes.route_id == route_id, 'route_long_name'].values[0]
            if route_name != target_route_name:
                continue
            print(trip_id)

            lat, lon = v.position.latitude, v.position.longitude

            if vehicle_id not in vehicle_state:
                trip_stops = stop_times[(stop_times.trip_id == trip_id)].merge(stops, on='stop_id')
                trip_stops['distance'] = trip_stops.apply(
                    lambda row: haversine(lat, lon, row['stop_lat'], row['stop_lon']), axis=1)

                
                nearest_stop = trip_stops.sort_values('distance').iloc[0]
                min_seq = nearest_stop['stop_sequence']
                remaining_stops = trip_stops[trip_stops['stop_sequence'] >= min_seq].sort_values('stop_sequence')
                # print(nearest_stop)
                vehicle_state[vehicle_id] = {
                    'prev_lat': lat,
                    'prev_lon': lon,
                    'remaining_stops': remaining_stops.reset_index(drop=True),
                    'last_stop_seq': min_seq - 1
                }
                continue  # skip this iteration since we just initialized

            state = vehicle_state[vehicle_id]
            if haversine(lat, lon, state['prev_lat'], state['prev_lon']) < 5:

                
                next_seq = state['last_stop_seq'] + 1
                remaining = state['remaining_stops']

                next_stop = remaining[remaining['stop_sequence'] == next_seq]
                if next_stop.empty:
                    continue
                next_stop = next_stop.iloc[0]

                stop_lat, stop_lon = next_stop['stop_lat'], next_stop['stop_lon']
                if haversine(lat, lon, stop_lat, stop_lon) < 5:
                    writer.writerow({
                        'vehicle_id': vehicle_id,
                        'route_id': route_id,
                        'route_name': route_name,
                        'trip_id': trip_id,
                        'stop_id': next_stop['stop_id'],
                        'stop_name': next_stop['stop_name'],
                        'stop_sequence': next_seq,
                        'stop_lat': stop_lat,
                        'stop_lon': stop_lon,
                        'arrival_date': now.strftime("%Y-%m-%d"),
                        'arrival_time': datetime.fromtimestamp(v.timestamp, ist).strftime("%H:%M:%S"),
                        'txt_arrival_time': next_stop['arrival_time']
                    })
                    print(f" Vehicle {vehicle_id} reached stop {next_stop['stop_id']} (seq {next_seq})")

                    state['prev_lat'] = lat
                    state['prev_lon'] = lon
                    state['last_stop_seq'] = next_seq
            else:
                vehicle_state[vehicle_id]['prev_lat'] = lat
                vehicle_state[vehicle_id]['prev_lon'] = lon

    time.sleep(30)

print("Logging complete.")
