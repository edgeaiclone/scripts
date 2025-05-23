import requests

# Step 1: Fetch live events data
live_events_url = "https://www.sofascore.com/api/v1/sport/tennis/events/live"

# Fetch live events
response = requests.get(live_events_url)
if response.status_code == 200:
    live_data = response.json()
    events = live_data.get('events', [])
    
    # Step 2: Prepare matches data dynamically
    matches_data = {}
    for event in events:
        match_id = event.get("id")
        home_player = event.get("homeTeam", {}).get("shortName", "Unknown Player")
        away_player = event.get("awayTeam", {}).get("shortName", "Unknown Player")
        matches_data[match_id] = {"home_player": home_player, "away_player": away_player}

    # Step 3: Initialize structured statistics container
    structured_stats = {
        "top": {
            "aces": [],
            "doubleFaults": [],
            "firstServeAccuracy": [],
            "secondServeAccuracy": [],
            "firstServePointsAccuracy": [],
            "secondServePointsAccuracy": [],
            "breakPointsSaved": []
        },
        "poor": {
            "aces": [],
            "doubleFaults": [],
            "firstServeAccuracy": [],
            "secondServeAccuracy": [],
            "firstServePointsAccuracy": [],
            "secondServePointsAccuracy": [],
            "breakPointsSaved": []
        }
    }

    # Step 4: Fetch statistics for each match ID
    base_statistics_url = "https://www.sofascore.com/api/v1/event/{}/statistics"

    for match_id, players in matches_data.items():
        try:
            # Construct the URL for statistics
            url = base_statistics_url.format(match_id)
            
            # Fetch the statistics data
            stats_response = requests.get(url)
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                statistics = stats_data.get("statistics", [])
                
                # Process the "ALL" period statistics
                for stat in statistics:
                    if stat.get("period") == "ALL":
                        for group in stat.get("groups", []):
                            for item in group.get("statisticsItems", []):
                                key = item.get("key")
                                home_player = players["home_player"]
                                away_player = players["away_player"]

                                # Add data to both `top` and `poor` (as placeholders for now)
                                if key == "aces":
                                    for category in ["top", "poor"]:
                                        structured_stats[category]["aces"].extend([
                                            {
                                                "player": home_player,
                                                "value": int(item.get("homeValue", 0)),
                                                "total": None,
                                                "percentage": None
                                            },
                                            {
                                                "player": away_player,
                                                "value": int(item.get("awayValue", 0)),
                                                "total": None,
                                                "percentage": None
                                            }
                                        ])
                                elif key == "doubleFaults":
                                    for category in ["top", "poor"]:
                                        structured_stats[category]["doubleFaults"].extend([
                                            {
                                                "player": home_player,
                                                "value": int(item.get("homeValue", 0)),
                                                "total": None,
                                                "percentage": None
                                            },
                                            {
                                                "player": away_player,
                                                "value": int(item.get("awayValue", 0)),
                                                "total": None,
                                                "percentage": None
                                            }
                                        ])
                                elif key == "firstServeAccuracy":
                                    for category in ["top", "poor"]:
                                        structured_stats[category]["firstServeAccuracy"].extend([
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
                                elif key == "secondServeAccuracy":
                                    for category in ["top", "poor"]:
                                        structured_stats[category]["secondServeAccuracy"].extend([
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
                                elif key == "firstServePointsAccuracy":
                                    for category in ["top", "poor"]:
                                        structured_stats[category]["firstServePointsAccuracy"].extend([
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
                                elif key == "secondServePointsAccuracy":
                                    for category in ["top", "poor"]:
                                        structured_stats[category]["secondServePointsAccuracy"].extend([
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
                                elif key == "breakPointsSaved":
                                    for category in ["top", "poor"]:
                                        structured_stats[category]["breakPointsSaved"].extend([
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

        except Exception as e:
            print(f"Error fetching data for Match ID {match_id}: {e}")

    # Print the structured statistics
    print(structured_stats)

else:
    print("Failed to retrieve live events data: ", response.status_code)
