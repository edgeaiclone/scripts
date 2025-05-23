import asyncio
from telethon import TelegramClient
from telethon.tl.functions.messages import DeleteMessagesRequest

# Telegram API Credentials
API_ID = "29007309"  # Replace with your actual API ID
API_HASH = "06eb6da7cfe017f97817cae62a139491"  # Replace with your actual API Hash
SESSION_NAME = "session_name"

DESTINATION_USER = "@bilalkhann16"  # User whose chat you want to delete

async def delete_chat_with_user():
    """Deletes all messages in the chat with the specified user."""
    try:
        async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
            # Get the entity (user) with whom you want to delete the chat
            user_entity = await client.get_entity(DESTINATION_USER)

            # Fetch the recent messages with that user (optional, but to ensure we have access to the chat)
            messages = await client.get_messages(user_entity, limit=100)  # You can adjust the limit

            # If there are messages, delete them
            if messages:
                message_ids = [msg.id for msg in messages]
                await client(DeleteMessagesRequest(message_ids))
                print(f"Deleted {len(message_ids)} messages from chat with {DESTINATION_USER}.")
            else:
                print(f"No messages found in the chat with {DESTINATION_USER}.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(delete_chat_with_user())
