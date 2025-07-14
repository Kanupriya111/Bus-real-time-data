# Bus-real-time-data
The main.py file in this repository aims to collect the real time GTFS data of bus travel.
The real-time GTFS data was fetched using an API which was further
filtered based on a given bus route ID, route name, and trip ID and
then checked if a vehicle is near the expected stop in the correct
sequence. For a given bus vehicle, the nearest stop was identified and
the sequence of upcoming stops were stored. On subsequent GPS
timestamps, if it was found that the vehicle hasn't moved more than
5 meters and is within 5 meters of the next stop in sequence, the
script logs the arrival details—such as stop ID, sequence of stop, GPS
arrival time, and scheduled arrival time—into a CSV file. This
ensured accurate stop-level logging while avoiding repeated entries
or out-of-sequence records. We then used this method to collect all
the data for other buses.

Here are the steps wise functionalty of the code in main.py :-
1) Importing Dependencies and Setting Up Paths:
The code begins by importing all necessary Python libraries for making HTTP requests, handling GTFS real-time data, working with dates and time zones, performing file operations, and calculating distances using geographic coordinates. It also sets up the path to access GTFS static files (routes.txt, stops.txt, stop_times.txt, and trips.txt) stored locally.

2) Reading and Merging GTFS Static Data:
The code loads the GTFS static files into pandas DataFrames and merges them to create a comprehensive dataset that includes trip IDs, route IDs, route names, stop sequences, stop names, and coordinates. This merged dataset is used later to compare and match real-time bus positions with scheduled stop information.

3) Time and Logging Setup:
A time window for logging is defined using the current time plus two hours. A CSV file is created (or appended to if it already exists) where the collected and filtered bus stop data will be saved.

4) Defining Haversine Distance Function:
A helper function is defined using the Haversine formula to compute the great-circle distance between two geographic coordinates. This is essential to determine how close a bus is to a given stop.

5) Initializing Vehicle Tracking Memory:
A dictionary is created to keep track of each vehicle’s last known position, the remaining stops it needs to reach on the route, and the last stop it successfully logged. This helps prevent duplicate logging and ensures the bus is progressing in the expected order of stops.

6) Polling the GTFS Real-time Feed:
Inside a loop, the script continuously sends HTTP requests to fetch the latest GTFS real-time data (in Protocol Buffers format). If the request fails, it waits a few seconds and retries. This process continues until the defined time window expires.

7) Filtering Relevant Vehicle Data:
Each real-time data entry is examined to extract the vehicle's ID, current position, route ID, and trip ID. Only those entries matching the targeted route and trip are processed further.

8) Initializing Vehicle’s Stop Sequence:
When a vehicle is encountered for the first time, its current position is compared with all scheduled stops in its trip. The stop closest to its current location is identified, and only the remaining stops from that point onward are kept for tracking. This ensures that the logging begins from the correct point in the route.

9) Detecting Stop Arrival and Logging:
For subsequent updates from the same vehicle, the script checks if the vehicle has remained within a small radius of its previous position (indicating a halt). If so, it then verifies whether the bus is near its next expected stop. If both conditions are met, it logs this stop’s details—along with the timestamp—into the output CSV.

10) Updating Vehicle State and Looping:
After processing, the vehicle’s last known position and stop sequence are updated. The loop then waits for a fixed interval (30 seconds in this case) before polling the real-time feed again, allowing time for the vehicle to move or reach the next stop. This cycle continues until the logging period ends.
