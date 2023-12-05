from datetime import datetime, timedelta
import sys
import firebase_admin
from firebase_admin import credentials, db
import googlemaps

# Firebase initialization
cred = credentials.Certificate('tab-tools-firebase-adminsdk-8ncav-4f5ccee9af.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://tab-tools-default-rtdb.firebaseio.com/'
})

# Realtime Database reference
ref = db.reference()
user_uid = sys.argv[1]
selected_del = sys.argv[2]

# print (user_uid,selected_del)
# Google Maps API initialization
google_maps_api_key = 'AIzaSyAwKbIHeqAYrgDWY9m7Oa-XNMW1kqqe5To'
gmaps = googlemaps.Client(key=google_maps_api_key)

user_data = ref.child('users').child(user_uid).get()
latitude = user_data.get('latitude', 0.0)
longitude = user_data.get('longitude', 0.0)

# Coordinates
coordinate1 = f"{latitude},{longitude}"

# Convert selected_del address to coordinates
geocode_result = gmaps.geocode(selected_del)
if geocode_result:
    selected_del_coordinates = geocode_result[0]['geometry']['location']
    coordinate2 = f"{selected_del_coordinates['lat']},{selected_del_coordinates['lng']}"
else:
    print(f"Error: Unable to geocode address '{selected_del}'.")
    sys.exit(1)
    
reverse_geocode_result = gmaps.reverse_geocode((latitude, longitude))
if reverse_geocode_result:
    address1 = reverse_geocode_result[0]['formatted_address']
else:
    print(f"Error: Unable to reverse geocode coordinates '{coordinate1}'.")
    sys.exit(1)

# Calculate distance and duration
directions_result = gmaps.directions(
    coordinate1,
    coordinate2,
    mode="driving",
    departure_time=datetime.now(),
)

# Extracting distance and duration
distance = directions_result[0]['legs'][0]['distance']['text']
duration_seconds = directions_result[0]['legs'][0]['duration']['value']

# Calculate ETA based on assumed speed (60 mph)
assumed_speed_mph = 60
duration_hours = duration_seconds / 3600
estimated_arrival_time = datetime.now() + timedelta(hours=duration_hours)

# Round ETA to the nearest 5-minute interval
rounded_eta = estimated_arrival_time + timedelta(minutes=5 - (estimated_arrival_time.minute % 5))

# Format ETA as MM/dd hh:mm
formatted_eta = rounded_eta.strftime("%m/%d %H:%M")

# Concatenate formatted_eta and address1
combined_data = f"{formatted_eta} divide {address1}"

# Update Realtime Database with combined data
ref.child('eta').child(user_uid).set(combined_data)

# Print the results
print(f"Starting Address: {address1}")
print(f"Destination Address: {selected_del}")
print(f"Distance: {distance}")
print(f"Duration: {duration_seconds} seconds ({duration_hours:.2f} hours)")
print(f"Estimated Arrival Time: {formatted_eta}")
print("ETA updated in the Realtime Database.")