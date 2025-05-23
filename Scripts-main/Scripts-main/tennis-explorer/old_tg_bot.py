# scrapping messages
from telethon import TelegramClient, events, sync
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPeerChannel, InputPeerUser
from telethon.tl.functions.messages import SendMessageRequest
from telethon.tl.types import InputPeerChannel
from telethon.errors import ChatWriteForbiddenError
import argparse
import json
import datetime
# from datetime import datetime  
import requests
# listenine to message events
from telethon.sync import TelegramClient
from telethon import events
from telethon.tl import types
import requests
import asyncio
import os
import os.path
import json
import csv
from datetime import date

from bson import ObjectId, json_util
from pymongo import MongoClient
import json
import argparse
import json
import requests
import google.auth.transport.requests
from google.oauth2 import service_account


PROJECT_ID = "edgeai-e42a0"
BASE_URL = "https://fcm.googleapis.com"
FCM_ENDPOINT = "v1/projects/" + PROJECT_ID + "/messages:send"
FCM_URL = BASE_URL + "/" + FCM_ENDPOINT
SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
SERVICE_ACCOUNT_FILE = "/home/ubuntu/edgeai-e42a0-firebase-adminsdk-ka5u0-b4bc1744c0.json"  



def change_dateformat(date_string):
    formatted_date = datetime.datetime.strptime(date_string, "%d.%m.%Y %H:%M")

    # formatted_date = datetime.datetime.strptime(date_string, "%d.%m.%Y")  # Convert to datetime object
    return formatted_date

def _get_access_token():
    """Retrieve a valid access token that can be used to authorize requests.

    :return: Access token.
    """
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token


def _send_fcm_message(fcm_message):
    """Send HTTP request to FCM with given message.

    Args:
      fcm_message: JSON object that will make up the body of the request.
    """

    headers = {
        "Authorization": "Bearer " + _get_access_token(),
        "Content-Type": "application/json; UTF-8",
    }
    # [END use_access_token]
    resp = requests.post(FCM_URL, data=json.dumps(fcm_message), headers=headers)

    if resp.status_code == 200:
        print("Message sent to Firebase for delivery, response:")
        print(resp.text)
    else:
        print("Unable to send message to Firebase")
        print(resp.text)

def _build_common_message(message_dict):
    """Construct common notifiation message.

    Construct a JSON object that will be used to define the
    common parts of a notification message that will be sent
    to any app instance subscribed to the news topic.
    """
    return  {
                "message": {
                    "topic": "live_mto",  
                    "notification": {
                        "title": "Live MTO",
                        "body": f"{message_dict['MTO_for']} - {message_dict['date']}",
                    },
                    "data": message_dict
                }}

def message_main(message_dict):
    parser = argparse.ArgumentParser()
    parser.add_argument("--message")
    args = parser.parse_args()
    common_message = _build_common_message(message_dict)
    print("FCM request body for message using common notification object:")
    # print(json.dumps(common_message, indent=2))
    _send_fcm_message(common_message)


api_id = '29007309'
api_hash = '06eb6da7cfe017f97817cae62a139491'

client = MongoClient("mongodb+srv://mayankchd10:LKWFSg3EX7GMmgJF@cluster0.gi3fv.mongodb.net")
db = client['edgeAI']
mto_collection = db.mtos

def parse_json(data):
    return json.loads(json_util.dumps(data))

# Initialize the Telegram client
client = TelegramClient('session_name', api_id, api_hash)
client.start()

# channel_to_scrape = 'https://t.me/+LHPMxRpOvMI1NzBk'
# channel_to_post_in = 'https://t.me/+MUWazDyBnLNhMWM0'
channel_to_scrape = 1659131863
channel_to_scrape = -1001659131863
# channel_to_post_in = "https://t.me/+C9FN-NeUMsk4MzM0"
channel_to_post_in = -1002110608217


# Extract the chat ID from the channel link
# get id of channel given link
def get_id(channel_link):
    # Extract the username from the channel link
    entity = client.get_entity(channel_link)
    # (types.Channel, types.Chat, types.User)
    # if isinstance(entity, (types.Channel, types.Chat)):
    channel_id = entity.id
    return channel_id


chat_id = get_id(channel_to_scrape)
# print(chat_id)


# Specify the channel link you want to scrape
# channel_link = ?
# specify the max number of messages you want to scrape
# max_messages  = ?

# scrape messages until limit is reached

async def scrape_channel_messages(max_messages=10, channel_link=channel_to_scrape):
    try:
        # Get the channel entity from the link
        channel_entity = await client.get_entity(channel_link)
        # Get the channel's message history
        offset_id = 0
        limit = 10
        all_messages = []
        total_messages = 0
        while True:
            # input_user = InputPeerUser(channel_entity.id, channel_entity.access_hash)
            input_channel = InputPeerChannel(channel_entity.id, channel_entity.access_hash)
            history = await client(GetHistoryRequest(
                peer=input_channel,
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
            messages = history.messages
            for message in messages:
                message_text = message.message
                if message_text and 'Date:' in message_text and 'Time:' in message_text:
                    message_parts = message_text.replace('**', '').split('\n\n')
                    print(message_parts)
                    msg_date = change_dateformat(message_parts)
                    try:
                        message_dict = {
                            'MTO_for': message_parts[0][1:],
                            'odds': 'Odds: ' + message_parts[5].split(': ')[1],
                            'scoreboard': 'Scoreboard: ' + message_parts[4].split(': ')[1],
                            'date': msg_date ,
                            'tournament': 'Tournament: ' + message_parts[3].split(': ')[1],
                            # 'time': message_parts[2].split(': ')[1],
                        }
                    except Exception as e:
                        print(e)
                    all_messages.append(message_dict)
                    mto_collection.insert_many(parse_json(all_messages))
            offset_id = messages[-1].id
            total_messages = len(all_messages)
            print(f'Retrieved {total_messages} messages so far...')
            if total_messages >= max_messages:
                break
        # Save the messages to a JSON file
        # filename = f'{channel_entity.title}_messages.json'
        # # saves messages to json of the specified name
        # save_messages_to_json(
        #     messages=all_messages[:max_messages], filename=filename)
        # filename = f'{channel_entity.title}_messages.csv'
        # save_messages_to_csv(
        #     all_messages=all_messages, filename=filename)
        
        if all_messages:
            await write_messages_to_channel(link=channel_to_post_in, messages=all_messages[::-1])
        # save_messages_to_json(
        #     messages=all_messages[:max_messages], filename='sent_msg.json')

        print(
            f'Scraping complete! {total_messages} messages saved.')
    except Exception as e:
        print(f'Error: {e}')

# scrape messages within the end_date and number of messages


async def scrape_channel_messages_by_date(end_date, channel_link=channel_to_scrape, max_messages=10):
    # fetches messages upto end date untill message limit is reached
    try:
        # Get the channel entity from the link
        channel_entity = await client.get_entity(channel_link)
        # Get the channel's message history
        offset_id = 0
        limit = 10
        all_messages = []
        total_messages = 0

        while True:
            history = await client(GetHistoryRequest(
                peer=InputPeerChannel(
                    channel_entity.id, channel_entity.access_hash),
                offset_id=offset_id,
                offset_date=(
                    end_date + datetime.timedelta(days=1)).timestamp(),
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))

            if not history.messages:
                break

            messages = history.messages

            for message in messages:
                message_text = message.message
                if message_text and 'Date:' in message_text and 'Time:' in message_text:
                    message_parts = message_text.replace('**', '').split('\n\n')
                    message_date = message.date
                    # if message_date >= start_datetime:
                    message_dict = {
                        'MTO_for':  message_parts[0][1:],
                        'odds': 'Odds: ' + message_parts[5].split(': ')[1],
                        'scoreboard': 'Scoreboard: ' + message_parts[4].split(': ')[1],
                        'date': 'Date: ' + message_parts[1].split(': ')[1],
                        'tournament': 'Tournament: ' + message_parts[3].split(': ')[1],
                        # 'time': message_parts[2].split(': ')[1],
                    }
                    all_messages.append(message_dict)

            offset_id = messages[-1].id
            total_messages = len(all_messages)
            print(f'Retrieved {total_messages} messages so far...')

            if total_messages >= max_messages:
                break

        # Save the messages to a JSON file
        filename = f'{channel_entity.title}_messages.json'
        save_messages_to_json(
            messages=all_messages[:max_messages], filename=filename)

        print(
            f'Scraping complete! {total_messages} messages saved to {filename}.')

    except Exception as e:
        print(f'Error: {e}')


# pass the link of the channel and a messages array  of the scaped format
async def write_messages_to_channel(link, messages):
    try:
        # Get the channel entity from the link
        channel_entity = await client.get_entity(link)
        existing_messages = []

        # Check if the file already exists and load its content
        try:
            with open('sent_msg.json', 'r', encoding='utf-8') as f:
                existing_messages = json.load(f)
        except FileNotFoundError:
            pass
        # Iterate over the list of messages
        for message in messages:
            try:
                if message not in existing_messages:
                    msg = f"{message['MTO_for']}\n\n{message['odds']}\n\n{message['scoreboard']}\n\n{message['date']}\n\n{message['tournament']}"
                    # Write the message to the channel
                    await client(SendMessageRequest(
                        peer=InputPeerChannel(
                            channel_entity.id, channel_entity.access_hash),
                        message=msg
                    ))
                    print(f"Message sent: {message}")
            except ChatWriteForbiddenError:
                print("Cannot write message. Write access to the channel is forbidden.")

    except Exception as e:
        print(f'Error: {e}')

# save array to json


def save_messages_to_json(messages, filename):
    existing_messages = []

    # Check if the file already exists and load its content
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            existing_messages = json.load(f)
    except FileNotFoundError:
        pass

    # Append new unique messages to the existing list
    for message in messages:
        if message not in existing_messages:
            existing_messages.append(message)

    # Save the updated list to the JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_messages, f, ensure_ascii=False, indent=2)

    print(f'{len(messages)} messages saved to {filename}.')

# save array to csv


def save_messages_to_csv(filename, all_messages):
    try:
        fieldnames = ['MTO_for', 'odds', 'scoreboard', 'date', 'tournament']

        # Check if the file already exists
        file_exists = os.path.isfile(filename)

        # Open the CSV file in append mode
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write the header row if the file is newly created
            if not file_exists:
                writer.writeheader()

            # Iterate through each message dictionary
            for message in all_messages:
                # Check if the message is already in the file
                if not is_message_in_csv(filename, message):
                    # Write the message dictionary to a new row in the CSV file
                    writer.writerow(message)

        print(f"Messages appended to {filename} successfully.")
    except Exception as e:
        print(e)

# helper for csv writer


def is_message_in_csv(filename, message):
    # Check if the message already exists in the CSV file
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if all(row[key] == message[key] for key in message.keys()):
                return True
    return False


current_date = date.today().day
# year-month-day
end_date = datetime.datetime(2024, 4, 23)


async def handle_new_message(event):
    try:
        # print('test',event.message.text, event.message.chat_id, type(event.message.chat_id) )

        # Check if the message is from the target channel
        if str(event.chat_id)[::-1][:len(str(chat_id))] == str(chat_id)[::-1]:
            print('target group found')
            message_text = event.message.text 
            # Print the new message
            if message_text and 'Date:' in message_text and 'Time:' in message_text:
                message_parts = message_text.replace('**', '').split('\n\n')
                print(message_parts,"-------------")
                date_string = message_parts[1].split(': ')[1]  # Extract "03.11.2024"

                message_date = change_dateformat(date_string)
                message_dict = {
                    'MTO_for': message_parts[0][1:],
                    'odds': 'Odds: ' + message_parts[5].split(': ')[1],
                    'scoreboard': 'Scoreboard: ' + message_parts[4].split(': ')[1],
                    'date': date_string,
                    'tournament': 'Tournament: ' + message_parts[3].split(': ')[1],
                    # 'time': message_parts[2].split(': ')[1],
                }
                mongo_message_dict = {
                    'MTO_for': message_parts[0][1:],
                    'odds': 'Odds: ' + message_parts[5].split(': ')[1],
                    'scoreboard': 'Scoreboard: ' + message_parts[4].split(': ')[1],
                    'date': message_date,
                    'tournament': 'Tournament: ' + message_parts[3].split(': ')[1],
                    # 'time': message_parts[2].split(': ')[1],
                }

                # filter_condition = {
                #     'MTO_for': message_dict['MTO_for'],
                #     'date': message_date,
                #     'tournament': message_dict['tournament']
                # }

                # Define update data
                update_data = {
                    '$set': {
                        'odds': mongo_message_dict['odds'],
                        'scoreboard': mongo_message_dict['scoreboard'],
                        'date': message_date,
                        'tournament': mongo_message_dict['tournament']
                    }
                }

                # Perform database update (Use await if using Motor)
                result = mto_collection.update_one(mongo_message_dict, update_data, upsert=True)
                stored_data = mto_collection.find_one(mongo_message_dict)

                if stored_data:
                    print("✅ Data stored successfully in DB:", stored_data)
                else:
                    print("❌ Data not found in DB!")
                # do operations like add to json csv or database
                channel_entity = await client.get_entity(channel_to_scrape)
                filename = f'{channel_entity.title}_messages.json'
                # save_messages_to_json(messages=[message_dict], filename=filename)

                # save_messages_to_csv(filename=filename,
                #                     all_messages=[message_dict])
                await write_messages_to_channel(link=channel_to_post_in, messages=[message_dict])
                save_messages_to_json(
                messages=[message_dict], filename='sent_msg.json')
                message_main(message_dict)
                print("Updated/Inserting message:", message_dict)

    except Exception as e:
        print(e, "Error handle_new_message")


async def main():
    print('Starting message scraper...')
    # await scrape_channel_messages()
    print("Listening for new messages...")

if __name__ == '__main__':
    #Start the client
    client.start()
    asyncio.get_event_loop().run_until_complete(main())
    with client:
        print('running')
        # Run the client until interrupted
        try:
            client.add_event_handler(handle_new_message, events.NewMessage())
            client.run_until_disconnected()
        except Exception as e:
            print(f'Error: {e}')
            
