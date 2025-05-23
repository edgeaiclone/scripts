import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from pymongo import MongoClient
import re
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Telegram API credentials
API_ID = "29007309"
API_HASH = "06eb6da7cfe017f97817cae62a139491"
SOURCE_CHANNEL_ID = -1001659131863  # Replace with your channel ID
DESTINATION_CHANNEL_ID = -1002110608217  # Replace with your destination channel ID

mongo_client = MongoClient("mongodb+srv://bilal:pLnClBIMtgJrn2jv@cluster0.gi3fv.mongodb.net")
db = mongo_client['edgeAI']
mto_collection = db.mtos

async def get_last_message(client):
    source_entity = await client.get_entity(SOURCE_CHANNEL_ID)
    destination_entity = await client.get_entity(DESTINATION_CHANNEL_ID)
    
    # Fetch the last message from the source channel
    history = await client(GetHistoryRequest(
        peer=source_entity,
        limit=1,
        offset_date=None,
        offset_id=0,
        max_id=0,
        min_id=0,
        add_offset=0,
        hash=0
    ))

    if not history.messages:
        logging.info("No messages found in the source channel.")
        return
    
    last_message = history.messages[0].message
    
    # Check if the message contains 'Medical timeout started for'
    if "Medical timeout started for" not in last_message:
        logging.info("The message does not contain the required text. Not sending.")
        return
    
    # Fetch the last message from the destination channel
    sent_messages = await client.get_messages(destination_entity, limit=1)
    last_sent_message = sent_messages[0].message if sent_messages else None
    

    if last_message != last_sent_message:
        mto_for_match = re.search(r"(🚑 .*?)\n", last_message)
        date_match = re.search(r"(📅 Date: [\d.]+)", last_message)
        time_match = re.search(r"(⏰️ Time: [\d:]+)", last_message)
        tournament_match = re.search(r"(🏆 Tournament: .+)", last_message)
        scoreboard_match = re.search(r"(🎾 Scoreboard: \([^)]+\))", last_message)
        odds_match = re.search(r"(💲 Odds: .+)", last_message)

        data = {
        "MTO_for": mto_for_match.group(1).strip() if mto_for_match else None,
        "date": date_match.group(1).strip() if date_match else None,
        "time": time_match.group(1).strip() if time_match else None,
        "tournament": tournament_match.group(1).strip() if tournament_match else None,
        "scoreboard": scoreboard_match.group(1).strip() if scoreboard_match else None,
        "odds": odds_match.group(1).strip()if odds_match else None,
        "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        message = (
        f"{data['MTO_for']}\n\n"
        f"{data['date']}\n\n"
        f"{data['time']}\n\n"
        f"{data['tournament']}\n\n"
        f"{data['scoreboard']}\n\n"
        f"{data['odds']}"
        )

        await client.send_message(destination_entity, message)
        mto_collection.insert_one(data)  # Insert the data into MongoDB
    else:
        logging.info("The last message received is the same as the last message sent.")

async def main():
    async with TelegramClient('session_name', API_ID, API_HASH) as client:
        while True:
            await get_last_message(client)
            await asyncio.sleep(5)  # Run every 5 seconds

asyncio.run(main())
