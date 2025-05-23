from pymongo import MongoClient


# MONGO_URI = "mongodb+srv://mayankchd10:LKWFSg3EX7GMmgJF@cluster0.gi3fv.mongodb.net/"
MONGO_URI = "mongodb+srv://bilal:pLnClBIMtgJrn2jv@cluster0.gi3fv.mongodb.net"
DATABASE_NAME = "edgeAI"
COLLECTION_NAME = "bets"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Find duplicate `iid` values
pipeline = [
    {"$group": {"_id": "$iid", "count": {"$sum": 1}, "docs": {"$push": "$_id"}}},
    {"$match": {"count": {"$gt": 1}}}
]

duplicates = list(collection.aggregate(pipeline))

if duplicates:
    print("Duplicate iid values found:")
    for dup in duplicates:
        print(f"iid: {dup['_id']}, Count: {dup['count']}, Docs: {dup['docs']}")
else:
    print("No duplicates found.")

client.close()
