import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from bson import ObjectId, json_util
from botasaurus.request import Request
import json
from tenacity import retry, stop_after_attempt, wait_fixed
from datetime import datetime, timezone
import re

def parse_json(data):
    return json.loads(json_util.dumps(data))

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

client = MongoClient(
    "mongodb+srv://bilal:pLnClBIMtgJrn2jv@cluster0.gi3fv.mongodb.net"
)
db = client["edgeAI"]
bets_collection = db.betmonitor

cookies = {
    'PHPSESSID': 'hs01tvh9atu342asm02i452ag4',
    'device': 'desktop',
    '_gid': 'GA1.2.1056866670.1723876859',
    '_gat_gtag_UA_151906320_1': '1',
    '_ga_3Y54V3BP8N': 'GS1.1.1723876858.1.0.1723876858.0.0.0',
    '_ga': 'GA1.1.2028666147.1723876859',
}

headers = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0',
  'Accept': '*/*',
  'Accept-Language': 'en-US,en;q=0.5',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'X-Requested-With': 'XMLHttpRequest',
  'Origin': 'https://www.betmonitor.com',
  'DNT': '1',
  'Connection': 'keep-alive',
  'Referer': 'https://www.betmonitor.com/dropping-odds',
  'Cookie': 'PHPSESSID=nhmdmlboicrkr3fd5ssin6uvn2; device=desktop',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-origin',
  'Sec-GPC': '1',
  'Priority': 'u=0'
}
payload = "market=1&time=2&bettype=all&sport=Tennis&limit=200"
url = "https://www.betmonitor.com/content/get_changes.php"

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_html():
    try:
        # response = Request().post('https://www.betmonitor.com/content/get_changes.php', cookies=cookies, headers=headers, data=data, timeout=10, verify=False)
        response = requests.request("POST", url, headers=headers, data=payload, cookies=cookies)
        if response.status_code == 200:
            html_content = response.text
            return html_content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def getData():
    try:
        html_content = get_html()
        if html_content is None:
            print("Failed to retrieve HTML content after retries.")
            return None
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract all event containers
        events = soup.find_all('div', class_='odds-changes-cont')
        new_ids = set()
        bets_collection.delete_many({})
        
        new_entries = []
        
        for event in events:
            date_info = event.find('div', class_='evtime').get_text(strip=True, separator=' ')
            league = event.find('div', class_='league').get_text(strip=True)
            teams = event.find('div', class_='teams').get_text(strip=True)
            odds = event.find('div', class_='odds').get_text(strip=True, separator=' ')
                # Extracting the odd drop percentage
            odd_drop_div = event.find('div', class_='value')
            if odd_drop_div:
                odd_drop_percentage = odd_drop_div.get_text(strip=True)
            else:
                odd_drop_percentage = "N/A"
                
            # Extracting the bet change
            change_div = event.find('div', class_='change')
            bet_change_1 = "N/A"
            bet_change_2 = "N/A"
            
            if change_div:
                change_elements = change_div.find_all('div')
                for index, change_element in enumerate(change_elements):
                    if 'highlight' in change_element.get('class', []):
                        if index == 0:
                            bet_change_1 = change_element.get_text(strip=True)
                        elif index == 1:
                            bet_change_2 = change_element.get_text(strip=True)

            try:
                odds = re.findall(r'\b\d+\.\d+\b', odds)
            except:
                print("Failed to extract odds")
                
            event_data = {
                "date": date_info,
                "league": league,
                "teams": teams,
                "odds": odds,
                "odd_drop": odd_drop_percentage,
                "bet_change_1": bet_change_1,
                "bet_change_2": bet_change_2,
                "created_at": datetime.now(timezone.utc)
            }
            new_entries.append(event_data)
            
        if new_entries:
            bets_collection.insert_many(new_entries)
            print(f"Inserted {len(new_entries)} new records.")
        else:
            print("No new data to insert.")
          
        print(f"Updated {len(new_ids)} records in MongoDB.")

    except Exception as e:
        print(e)

getData()