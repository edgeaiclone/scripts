import asyncio
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from pymongo import MongoClient
import re

# Telegram API Credentials
API_ID = "29007309"
API_HASH = "06eb6da7cfe017f97817cae62a139491"
SESSION_NAME = "session_name"

# Telegram Channels
SOURCE_CHANNEL_ID = -1001659131863
DESTINATION_CHANNEL = -1002110608217

# MongoDB Connection
mongo_client = MongoClient("mongodb+srv://bilal:pLnClBIMtgJrn2jv@cluster0.gi3fv.mongodb.net")
db = mongo_client['edgeAI']
mto_collection = db.mtos

def is_structured_message(text):
    """Check if the message follows the structured format (first format)."""
    return bool(re.search(r"🚑 Medical timeout started for .*!", text))

async def scrape_today_messages(client):
    """Fetches today's messages from the source Telegram channel and sends them to the destination."""
    try:
        channel_entity = await client.get_entity(SOURCE_CHANNEL_ID)
        offset_id = 0
        limit = 100  # Fetch in batches
        all_messages = []
        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        while True:
            history = await client(GetHistoryRequest(
                peer=channel_entity,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))

            if not history.messages:
                break

            for message in history.messages:
                if message.date and message.message:
                    msg_date = message.date.strftime("%Y-%m-%d")
                    if msg_date == today_date:
                        message_data = {
                            'text': message.message,
                            'date': msg_date,
                            'message_id': message.id
                        }
                        all_messages.append(message_data)
                    else:
                        break

            offset_id = history.messages[-1].id  # Update offset to fetch older messages

            # Stop fetching if messages are from a previous day
            if history.messages[-1].date.strftime("%Y-%m-%d") != today_date:
                break

        if all_messages:
            new_messages = []
            sent_messages = await client.get_messages(DESTINATION_CHANNEL, limit=100)
            sent_texts = {sent_msg.text for sent_msg in sent_messages if sent_msg.text}

            for msg in all_messages:
                if msg['text'] not in sent_texts:
                    new_messages.append(msg)

            if new_messages:
                print(f"[{datetime.now()}] Sending {len(new_messages)} new messages...")
                await send_messages_to_user(client, DESTINATION_CHANNEL, new_messages)
            else:
                print(f"[{datetime.now()}] No new messages to send.")

        else:
            print(f"[{datetime.now()}] No messages found for today.")

    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")

async def insert_to_mongo(text):
    print ('text', text)
    """Extracts information from text and inserts into MongoDB."""
    main_message_pattern = r"^(.*?)\n\n"
    date_pattern = r"📅 Date: (\d{2}\.\d{2}\.\d{4})"
    time_pattern = r"⏰️ Time: ([\d:]+)"
    tournament_pattern = r"🏆 Tournament: (.*?)(?=\n|$)"
    scoreboard_pattern = r"🎾 Scoreboard: (\([^\)]+\))"
    odds_pattern = r"💲 Odds: ([^ Against]+ Against.*)"

    main_message = re.search(main_message_pattern, text)
    date = re.search(date_pattern, text)
    time = re.search(time_pattern, text)
    tournament = re.search(tournament_pattern, text)
    scoreboard = re.search(scoreboard_pattern, text)
    odds = re.search(odds_pattern, text)

    mto_collection.insert_one({
        'MTO_for': main_message.group(1).strip() if main_message else 'Something went wrong, please check the logs.',
        'odds': odds.group(1).strip() if odds else None,
        'scoreboard': scoreboard.group(1) if scoreboard else None,
        'date': date.group(1) if date else None,
        'tournament': tournament.group(1) if tournament else None,
        'createdAt': datetime.now(timezone.utc)
    })

async def send_messages_to_user(client, username, messages):
    """Sends new messages to the destination channel."""
    try:
        user_entity = await client.get_entity(username)
        for message in messages:
            text = message['text']

            if is_structured_message(text):
                await client.send_message(user_entity, text)
                await insert_to_mongo(text)
                print(f"[{datetime.now()}] Structured message sent successfully!")
            else:
                print(f"[{datetime.now()}] Skipped unstructured message.")

    except Exception as e:
        print(f"[{datetime.now()}] Error sending messages: {e}")

async def main():
    """Runs the scraper every 5 seconds."""
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        while True:
            await scrape_today_messages(client)
            await asyncio.sleep(5)  # Wait 5 seconds before next run

if __name__ == "__main__":
    asyncio.run(main())
