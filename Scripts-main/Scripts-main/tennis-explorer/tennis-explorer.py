import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from tenacity import retry, stop_after_attempt, wait_fixed
from bson import ObjectId, json_util
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
retired_player_collection = db.retiredplayers

url = "https://www.tennisexplorer.com/list-players/injured/"

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_player_data():
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return None

def parse_injured_players(soup):
    injured_players = []
    table = soup.find("table", class_="result flags injured")
    if not table:
        logging.warning("No data table found.")
        return injured_players

    for row in table.find("tbody").find_all("tr"):
        start_date = row.find("td", class_="first time noWrp").text.strip()
        name_element = row.find("td", class_="t-name")
        name = name_element.text.strip()
        player_profile_link = "https://www.tennisexplorer.com" + name_element.find("a")["href"]
        tournament = row.find("td", class_="tl tournament").text.strip()
        reason = row.find("td", class_="reason").text.strip()

        injured_players.append({
            "start_date": start_date,
            "name": name,
            "tournament": tournament,
            "reason": reason,
            "profile_link": player_profile_link
        })
    return injured_players

def get_player_matches(profile_url):
    match_info_list = []
    profile_response = requests.get(profile_url)
    player_soup = BeautifulSoup(profile_response.content, "html.parser")
    matches_div = player_soup.find("div", id="matches-2024-1-data")
    if not matches_div:
        logging.warning("No matches found for the player.")
        return match_info_list

    result_table = matches_div.find("table", class_="result balance")
    if not result_table:
        return match_info_list

    head_row = result_table.find("tr", class_="head flags")
    tournament_name = head_row.find("td", class_="t-name").text.strip() if head_row else "N/A"

    for match_row in result_table.find_all("tr", class_=["one", "two"]):
        match_date_element = match_row.find("td", class_="first time")
        surface_element = match_row.find("td", class_="s-color")
        opponents_element = match_row.find("td", class_="t-name")
        round_element = match_row.find("td", class_="round")
        result_element = match_row.find("td", class_="tl")
        odds_elements = match_row.find_all("td", class_="course")

        match_date = match_date_element.text.strip() if match_date_element else "N/A"
        surface = (surface_element.find("span")["title"] if surface_element and surface_element.find("span") and 'title' in surface_element.find("span").attrs else "N/A")
        opponents = opponents_element.text.strip() if opponents_element else "N/A"
        round_info = round_element.get("title", "") if round_element else "N/A"
        match_result = result_element.text.strip() if result_element else "N/A"
        odds1 = odds_elements[0].text.strip() if len(odds_elements) > 0 else "N/A"
        odds2 = odds_elements[1].text.strip() if len(odds_elements) > 1 else "N/A"

        match_info_list.append({
            "tournament": tournament_name,
            "match_date": match_date,
            "surface": surface,
            "opponents": opponents,
            "round": round_info,
            "result": match_result,
            "odds1": odds1,
            "odds2": odds2
        })
    return match_info_list

def update_database(injured_players):
    if injured_players:
        retired_player_collection.delete_many({})
    for player in injured_players:
        player["matches"] = get_player_matches(player["profile_link"])
        retired_player_collection.update_one(
            {"name": player["name"]},
            {"$set": player},
            upsert=True
        )

def get_data():
    soup = get_player_data()
    if not soup:
        logging.error("Failed to fetch data.")
        return
    injured_players = parse_injured_players(soup)
    update_database(injured_players)

if __name__ == "__main__":
    get_data()
