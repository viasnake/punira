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
        query = context.content
        user = context.author.display_name
        user_id = str(context.author.id)
        channel_id = str(context.channel.id)
        try:
            response = await self.GetResponse(
                self.bot,
                query,
                user,
                user_id,
                channel_id
            )
        except Exception as e:
            await context.reply(f"{str(e)}")
            self.bot.logger.error(f"{str(e)}, Query: {query}, User: {user}, Channel ID: {channel_id}")
            return
        if not response:
            return

        # Send the response
        await context.reply(response)

    async def GetResponse(self, bot, query: str, user: str, user_id: str, channel_id: str) -> str:

        # Get the conversation ID
        conversation_id = await self.GetConversationIdByChannelId(channel_id)
        data = {
            "inputs": {
                "username": user,
            },
            "query": query,
            "response_mode": "blocking",
            "conversation_id": conversation_id,
            "user": channel_id,  # Does not support multiple users
        }

        # Send the request
        response = await self.SendApiRequest(bot, data)

        # If the conversation ID is invalid, retry with an empty conversation ID
        if response.status_code == 404 and response.json().get("message") == "Conversation Not Exists.":
            # Retry with empty conversation ID
            conversation_id = ""
            data["conversation_id"] = ""
            response = await self.SendApiRequest(bot, data)

        # If the response is not valid, raise an exception
        if response.status_code != 200:
            self.bot.logger.error(f"API request failed with status code {response.status_code}, response: {response.text}, URL: {response.url}")
            raise Exception(f"API request failed with status code {response.status_code}")
        response_json = response.json()

        # If the response is not valid, raise an exception
        if "answer" not in response_json or not response_json["answer"]:
            self.bot.logger.error(f"No valid response received from the API, response: {response.text}, URL: {response.url}")
            raise Exception("No valid response received from the API")

        # Save the conversation ID
        if not conversation_id:
            await self.SaveConversationId(user_id, channel_id, response_json["conversation_id"])

        # Return the response
        return response_json["answer"]

    async def SendApiRequest(self, bot, data: dict) -> requests.Response:
        headers = {
            'Authorization': f'Bearer {bot.config["API_KEY"]}',
            'Content-Type': 'application/json'
        }
        API_URL = bot.config["API_URL"] + "/chat-messages"
        response = requests.post(
            API_URL,
            headers=headers,
            json=data,
        )
        return response

    async def SaveConversationId(self, user_id: str, channel_id: str, conversation_id: str) -> None:

        # File format:
        # user_id:channel_id:conversation_id
        # if the user ID is not available, it will be set to 0

        # Save the conversation ID
        with open("conversation_id.txt", "a") as file:
            file.write(f"{user_id}:{channel_id}:{conversation_id}\n")

    async def GetConversationIdByChannelId(self, channel_id: str) -> str:

        # Get the conversation ID
        conversation_id = ""
        with open("conversation_id.txt", "r") as file:
            for line in file:
                _, temp_channel_id, temp_conversation_id = line.split(":")
                if temp_channel_id == channel_id:
                    conversation_id = temp_conversation_id
                    break
        conversation_id = conversation_id.rstrip("\n")

        # Return the conversation ID
        return conversation_id

async def setup(bot):
    await bot.add_cog(Chat(bot))
