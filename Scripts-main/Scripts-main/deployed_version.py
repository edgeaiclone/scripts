import requests
from pymongo import MongoClient
from datetime import datetime

# Define proxies
# proxies = {
#     'http': 'socks5h://127.0.0.1:9050',
#     'https': 'socks5h://127.0.0.1:9050'
# }

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com"
}

def fetch_live_events(url):
    response = requests.get(url, headers = headers)  # Add proxies here
    if response.status_code == 200:
        return response.json().get('events', [])
    else:
        print("Failed to retrieve live events data:", response.status_code)
        return []

def prepare_matches(events):
    matches = {}
    for event in events:
        match_id = event.get("id")
        home_player = event.get("homeTeam", {}).get("shortName", "Unknown Player")
        away_player = event.get("awayTeam", {}).get("shortName", "Unknown Player")
        matches[match_id] = {"home_player": home_player, "away_player": away_player}
    return matches

def fetch_statistics(match_id, base_url):
    try:
        url = base_url.format(match_id)
        response = requests.get(url, proxies=proxies, headers = headers)  # Add proxies here
        if response.status_code == 200:
            return response.json().get("statistics", [])
    except Exception as e:
        print(f"Error fetching data for Match ID {match_id}: {e}")
    return []

def process_statistics(statistics, players, structured_stats):
    if "breakPointsSaved1" not in structured_stats["poor"]:
        structured_stats["poor"]["breakPointsSaved1"] = []  # Initialize as empty list for "poor" category

    for stat in statistics:
        if stat.get("period") == "ALL":
            for group in stat.get("groups", []):
                for item in group.get("statisticsItems", []):
                    key = item.get("key")
                    home_player = players["home_player"]
                    away_player = players["away_player"]

                    # Keys to process
                    if key in [
                        "firstServeAccuracy", "secondServeAccuracy", 
                        "firstServePointsAccuracy", "secondServePointsAccuracy", 
                        "breakPointsSaved", "aces", "doubleFaults", "receiverPointsScored"
                    ]:
                        for category in ["top", "poor"]:
                            # Exclude specific keys from certain categories
                            if category == "top" and key == "breakPointsSaved":
                                continue
                            if category == "poor" and key == "aces":
                                continue
                            if category == "top" and key == "doubleFaults":
                                continue
                            if category == "top" and key == "receiverPointsScored":
                                continue

                            structured_stats[category][key].extend([
                                {
                                    "player": home_player,
                                    "value": int(item.get("homeValue", 0)),
                                    "total": int(item.get("homeTotal", 0)),
                                    "percentage": round((int(item.get("homeValue", 0)) / int(item.get("homeTotal", 1))) * 100, 2) if item.get("homeTotal") else None
                                },
                                {
                                    "player": away_player,
                                    "value": int(item.get("awayValue", 0)),
                                    "total": int(item.get("awayTotal", 0)),
                                    "percentage": round((int(item.get("awayValue", 0)) / int(item.get("awayTotal", 1))) * 100, 2) if item.get("awayTotal") else None
                                }
                            ])

                    # Additional logic for breakPointsSaved1 (only for "poor" category)
                    if key == "breakPointsSaved":
                        for category in ["poor"]:
                            structured_stats[category]["breakPointsSaved1"].extend([
                                {
                                    "player": home_player,
                                    "value": int(item.get("homeTotal")) - int(item.get("homeValue")),  # total - value
                                    "percentage": None  # Set percentage to None
                                },
                                {
                                    "player": away_player,
                                    "value": int(item.get("awayTotal", )) -  int(item.get("awayValue", )),
                                    "percentage": None  # Set percentage to None
                                }
                            ])

def apply_filters(structured_stats):
    filters = [
        ("top", "aces", 3, 100, True),
        ("poor", "doubleFaults", 3, 100, True),
        ("top", "firstServeAccuracy", 60, 10, True),
        ("top", "secondServeAccuracy", 60, 10, True),
        ("top", "firstServePointsAccuracy", 60, 7, True),
        ("top", "secondServePointsAccuracy", 60, 4, True),
        ("poor", "firstServeAccuracy", 60, 10, False),
        ("poor", "secondServeAccuracy", 60, 5, False),
        ("poor", "firstServePointsAccuracy", 60, 7, False),
        ("poor", "secondServePointsAccuracy", 60, 4, False),
        ("poor", "breakPointsSaved", 60, 3, False),
        ("poor", "receiverPointsScored", 3, 16, False),
        ("poor", "breakPointsSaved1", 100, 300, False),
    ]
    
    for category, key, min_threshold, max_threshold, is_top in filters:
        if key == "breakPointsSaved1":
            for stat in structured_stats["poor"].get(key, []):
                if stat["value"] > 2:
                    stat["percentage"] = None
                else:
                    stat["total"] = 0
                    stat["percentage"] = "0"

            structured_stats["poor"][key] = sorted(
                [stat for stat in structured_stats["poor"].get(key, []) if stat["value"] > 2],
                key=lambda x: x["value"],  # Sort by 'value'
                reverse=True  # Sort in descending order
            )[:5]

        elif key in ["doubleFaults"]:
            structured_stats[category][key] = sorted(
                [
                    player for player in structured_stats[category][key]
                    if (
                        (min_threshold is None or player["value"] > min_threshold) and
                        (max_threshold is None or player["value"] <= max_threshold)
                    )
                ],
                key=lambda x: x["value"],
                reverse=(category == "poor")
            )[:5]

        elif key in ["aces", "receiverPointsScored", "breakPointsScored"]:
            structured_stats[category][key] = sorted(
                [
                    player for player in structured_stats[category][key]
                    if (
                        (min_threshold is None or player["value"] > min_threshold) and
                        (max_threshold is None or player["value"] <= max_threshold)
                    )
                ],
                key=lambda x: x["value"],
                reverse=(category == "top")
            )[:5]

        else:
            structured_stats[category][key] = sorted(
                [
                    player for player in structured_stats[category][key]
                    if player["percentage"] and (
                        (player["percentage"] > min_threshold if is_top else player["percentage"] < min_threshold)
                    ) and player["total"] > max_threshold
                ],
                key=lambda x: x["percentage"],
                reverse=is_top
            )[:5]

def clean_and_insert_to_mongo(db_name, collection_name, data):
    print ('data.length', len (data))
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    connection_string = "mongodb+srv://bilal:pLnClBIMtgJrn2jv@cluster0.gi3fv.mongodb.net/"

    client = MongoClient(connection_string)
    db = client[db_name]
    collection = db[collection_name]
    collection.delete_many({})  # Clear existing data
    collection.insert_one(data)  # Insert the new structured data
    print(f"Data has been cleaned and inserted into MongoDB. Timestamp: {current_time}")

def swap_break_points_scored(structured_stats):
    if "breakPointsScored" in structured_stats["poor"]:
        break_points_scored = structured_stats["poor"]["breakPointsScored"]
        
        if len(break_points_scored) == 2:
            break_points_scored[0]["value"], break_points_scored[1]["value"] = break_points_scored[1]["value"], break_points_scored[0]["value"]

def main():
    live_events_url = "https://www.sofascore.com/api/v1/sport/tennis/events/live"
    base_statistics_url = "https://www.sofascore.com/api/v1/event/{}/statistics"

    events = fetch_live_events(live_events_url)

    matches_data = prepare_matches(events)

    structured_stats = {
        "top": {
            "aces": [],
            "firstServeAccuracy": [],
            "secondServeAccuracy": [],
            "firstServePointsAccuracy": [],
            "secondServePointsAccuracy": [],
        },
        "poor": {
            "doubleFaults": [],
            "firstServeAccuracy": [],
            "secondServeAccuracy": [],
            "firstServePointsAccuracy": [],
            "secondServePointsAccuracy": [],
            "breakPointsSaved": [],
            "receiverPointsScored": [],
            "breakPointsSaved1": []  # for broken on serve
        }
    }

    for match_id, players in matches_data.items():
        statistics = fetch_statistics(match_id, base_statistics_url)
        process_statistics(statistics, players, structured_stats)

    apply_filters(structured_stats)

    # Clean MongoDB collection and insert data
    clean_and_insert_to_mongo("edgeAI", "livestats", structured_stats)

if __name__ == "__main__":
    main()