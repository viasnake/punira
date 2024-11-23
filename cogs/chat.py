import discord
import requests
from discord.ext import commands
from discord.ext.commands import Context

class Chat(commands.Cog, name="Chat"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def chat(self, context: Context) -> None:
        # Check if the message is valid
        ALLOWED_CHANNEL_NAMES = ["punira"]
        if not any(
            context.channel.name.startswith(channel_name)
            for channel_name in ALLOWED_CHANNEL_NAMES
        ):
            return
        if not any(mention.id == self.bot.user.id for mention in context.mentions):
            return
        if context.author.bot:
            return
        if context.attachments:
            return

        # Format the message
        context.content = context.content.replace(f"<@{self.bot.user.id}>", "")
        context.content = context.content.strip()
        for mention in context.mentions:
            context.content = context.content.replace(
                f"<@{mention.id}>", mention.display_name
            )

        # Limit the message length
        if len(context.content) > 300:
            return

        # Get the response from the API
        user = context.author.display_name
        query = context.content
        channel_id = str(context.channel.id)
        try:
            response = await GetResponse(self.bot, query, user, channel_id)
        except Exception as e:
            await context.reply(f"{str(e)}")
            return
        if not response:
            return

        # Send the response
        await context.reply(response)


async def GetResponse(bot, query: str, user: str, channel_id: str) -> str:

    # Get the conversation ID
    conversation_id = await GetConversationId(channel_id)
    headers = {
        'Authorization': f'Bearer {bot.config["API_KEY"]}',
        'Content-Type': 'application/json'
    }
    data = {
        "inputs": {
            "username": user,
        },
        "query": query,
        "response_mode": "blocking",
        "conversation_id": conversation_id,
        "user": user,
    }
    API_URL = bot.config["API_URL"] + "/chat-messages"

    # Send the request
    response = requests.post(
        API_URL,
        headers=headers,
        json=data,
    )

    # Check the response
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")
    response_json = response.json()
    if "answer" not in response_json or not response_json["answer"]:
        raise Exception("No valid response received from the API")
    if not conversation_id:
        await SaveConversationId(channel_id, response_json["conversation_id"])

    # Return the response
    return response_json["answer"]

async def SaveConversationId(channel_id: str, conversation_id: str) -> None:

    # Save the conversation ID
    with open("conversation_id.txt", "a") as file:
        pass
    with open("conversation_id.txt", "a") as file:
        file.write(f"{channel_id}:{conversation_id}\n")

async def GetConversationId(channel_id: str) -> str:

    # Get the conversation ID
    conversation_id = ""
    with open("conversation_id.txt", "r") as file:
        for line in file:
            temp_channel_id, temp_conversation_id = line.split(":")
            if channel_id == temp_channel_id:
                conversation_id = temp_conversation_id
    conversation_id = conversation_id.rstrip("\n")

    # Return the conversation ID
    return conversation_id

async def setup(bot):
    await bot.add_cog(Chat(bot))
