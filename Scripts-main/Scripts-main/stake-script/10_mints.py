import os
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone

# Load MongoDB URI from environment variables
MONGO_URI = "mongodb+srv://mayankchd10:LKWFSg3EX7GMmgJF@cluster0.gi3fv.mongodb.net/"  # Store this in environment variables
DATABASE_NAME = "edgeAI"
COLLECTION_NAME = "bets"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

ten_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=20)

# Convert ten_minutes_ago to a string format matching your data
ten_minutes_ago_str = ten_minutes_ago.strftime("%a, %d %b %Y %H:%M:%S GMT")

# Query MongoDB (filter by `createdAt` instead of `timestamp`)
recent_data = collection.find({"createdAt": {"$gte": ten_minutes_ago_str}})

# Convert cursor to list and check if empty
recent_data_list = list(recent_data)
print(f"Found {len(recent_data_list)} records in the last 10 minutes.")

# Print results

initial_data = ["sport:296809881", "sport:2968098812"]

#check if initial data is in recent data list. If found, remove the string from initial data
#initial data has is list of strings with uuid, we need to check if any of these uuids are present in the recent data list, if present, remove pirticular uuid from initial data list
for data in recent_data_list:
    if data["iid"] in initial_data:
        initial_data.remove(data["iid"])

print (initial_data)