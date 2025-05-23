import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from bson import ObjectId, json_util
import json
from datetime import datetime
import time
import threading

# Helper function to parse MongoDB documents into JSON format
def parse_json(data):
    return json.loads(json_util.dumps(data))


# Custom JSON Encoder to handle ObjectId serialization
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


# Connect to MongoDB
client = MongoClient(
    "mongodb+srv://bilal:pLnClBIMtgJrn2jv@cluster0.gi3fv.mongodb.net"
)
db = client["edgeAI"]
returning_player_collection = db.returnedPlayers
returning_player_history_collection = db.returnedPlayersHistory

# Scrape the returning players data
url = "https://www.tennisexplorer.com/list-players/return-from-injury/"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

def convert_return_date(date_str: str) -> str:
    """
    Converts a date string from DD.MM.YYYY format to ISO 8601 format (YYYY-MM-DDTHH:mm:ss.sssZ).
    
    :param date_str: Date in DD.MM.YYYY format
    :return: Date in ISO 8601 format
    """
    try:
        date_obj = datetime.strptime(date_str, "%d.%m.%Y")
        return date_obj
        # date_obj = datetime.strptime(date_str, "%d.%m.%Y")
        # iso_date = date_obj.isoformat() + "Z"
        # return iso_date
    except ValueError:
        return None
def get_data():
    # Extract the data from the table
    returning_players = []
    table = soup.find("table", class_="result flags injured")

    for row in table.find("tbody").find_all("tr"):
        return_date = row.find("td", class_="first time noWrp").text.strip()
        name_element = row.find("td", class_="t-name")
        name = name_element.text.strip()
        player_profile_link = "https://www.tennisexplorer.com" + name_element.find("a")["href"]
        tournament = row.find("td", class_="tl tournament").text.strip()
        return_date_obj = convert_return_date(return_date)
        returning_players.append({
            "return_date": return_date_obj,
            "name": name,
            "tournament": tournament,
            "profile_link": player_profile_link
        })


    # Function to scrape match data from the player's profile
    def get_player_matches(profile_url):
        match_info_list = []

        # Send request to player's profile page
        profile_response = requests.get(profile_url)
        player_soup = BeautifulSoup(profile_response.content, "html.parser")

        # Find the relevant div containing match data (adjust year if necessary)
        matches_div = player_soup.find("div", id="matches-2025-1-data")
        if matches_div:
            result_table = matches_div.find("table", class_="result balance")
            result_table= result_table if result_table else matches_div.find("table", class_="result gamedetail")
            if result_table:
                # Extract tournament name from the "head flags" row
                head_row = result_table.find("tr", class_="head flags")
                tournament_name = head_row.find("td", class_="t-name").text.strip() if head_row else "N/A"
                
                for match_row in result_table.find_all("tr", class_=["one", "two"]):
                    # Safely extract match information
                    match_date_element = match_row.find("td", class_="first time")
                    surface_element = match_row.find("td", class_="s-color")
                    opponents_element = match_row.find("td", class_="t-name")
                    round_element = match_row.find("td", class_="round")
                    result_element = match_row.find("td", class_="tl")
                    odds_elements = match_row.find_all("td", class_="course")

                    # Extract only if the element exists
                    match_date = match_date_element.text.strip() if match_date_element else "N/A"

                    # Handling surface safely
                    surface = "N/A"
                    if surface_element:
                        span_element = surface_element.find("span")
                        surface = span_element['title'] if span_element and 'title' in span_element.attrs else "N/A"
                    
                    opponents = opponents_element.text.strip() if opponents_element else "N/A"
                    round_info = round_element.get("title", "") if round_element else "N/A"
                    match_result = result_element.text.strip() if result_element else "N/A"
                    odds1 = odds_elements[0].text.strip() if len(odds_elements) > 0 else "N/A"
                    odds2 = odds_elements[1].text.strip() if len(odds_elements) > 1 else "N/A"

                    match_info = {
                        "tournament": tournament_name,  # Add tournament name to each match
                        "match_date": match_date,
                        "surface": surface,
                        "opponents": opponents,
                        "round": round_info,
                        "result": match_result,
                        "odds1": odds1,
                        "odds2": odds2
                    }
                    # print(match_info)
                    if len(match_info_list) < 2:  # Limiting to two matches
                        match_info_list.append(match_info)
        else:
            print("No match data found for the given player.")
        return match_info_list


    # Convert the list of players to JSON and print

    
    # Insert or update each player's data into MongoDB and scrape match data
    if len(returning_players)> 0:
        returning_player_collection.delete_many({})
    for player in returning_players:
        # Scrape match data for the player
        # print(player["profile_link"])
        matches = get_player_matches(player["profile_link"])
        player["matches"] = matches
        # print(player)

        #add current date and time to the player for tracking
        player["created_at"] = datetime.now()
        returning_player_collection.insert_one(player)

        result = returning_player_collection.update_one(
            {"name": player["name"], "return_date": player["return_date"]},  
            {"$set": player},  # Fields to update or insert
            upsert=True 
        )
      
        player_copy = player.copy() 
        player_copy.pop("_id", None) 
        result = returning_player_history_collection.update_one(
            {"name": player["name"], "return_date": player["return_date"]},  
            {"$set": player_copy},  # Fields to update or insert
            upsert=True 
        )
        # Print operation result
        # print(f"Upserted {player['name']} - Matched: {result.matched_count}, Modified: {result.modified_count}")


try:
    get_data()
    print ("Data inserted successfully at time: ", datetime.now())
except Exception as e:
    print(e)