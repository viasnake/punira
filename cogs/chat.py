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

        #
        query = context.content
        user = context.author.display_name
        user_id = str(context.author.id)
        channel_id = str(context.channel.id)

        # Check the query
        try:
            await self.CheckQuery(query)
        except Exception as e:
            await context.reply(f"{str(e)}")
            return

        # Get the response
        try:
            response = await self.GetResponse(
                self.bot,
                query,
                user,
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

    async def GetResponse(self, bot, query: str, user: str, channel_id: str) -> str:

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
        answer = response_json["answer"]

        # If the response is not valid, raise an exception
        if "answer" not in response_json or not answer:
            self.bot.logger.error(f"No valid response received from the API, response: {response.text}, URL: {response.url}")
            raise Exception("No valid response received from the API")

        # Check the response text
        await self.CheckResponseText(answer)

        # Save the conversation ID
        if not conversation_id:
            await self.SaveConversationId(channel_id, response_json["conversation_id"])

        # Parse the response message
        response_message = await self.ParseResponseMessage(answer)

        # Return the response message
        return response_message

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

    async def SaveConversationId(self, channel_id: str, conversation_id: str) -> None:

        # File format:
        # channel_id:conversation_id
        # if the user ID is not available, it will be set to 0

        # Save the conversation ID
        with open("conversation_id.txt", "a") as file:
            file.write(f"{channel_id}:{conversation_id}\n")

    async def GetConversationIdByChannelId(self, channel_id: str) -> str:

        # If file does not exist, create it and return an empty string
        with open("conversation_id.txt", "a") as file:
            pass

        # Get the conversation ID
        conversation_id = ""
        with open("conversation_id.txt", "r") as file:
            for line in file:
                temp_channel_id, temp_conversation_id = line.split(":")
                if temp_channel_id == channel_id:
                    conversation_id = temp_conversation_id
                    break
        conversation_id = conversation_id.rstrip("\n")

        # Return the conversation ID
        return conversation_id

    async def ParseResponseMessage(self, message: str) -> str:

        # Message format:
        # <出力><発言>This is the response message</発言></出力>
        # Return format:
        # This is the response message

        # Parse the XML message
        message = message.replace("<出力>", "")
        message = message.replace("</出力>", "")
        message = message.replace("<発言>", "")
        message = message.replace("</発言>", "")

        # Return the message
        return message

    async def CheckQuery(self, query: str) -> None:

        # Check if the query is valid
        if not query:
            raise Exception("Query is empty")
        if len(query) > 300:
            raise Exception("Query is too long")

        # Check XML tags
        if "<" in query and ">" in query:
            if query.index("<") < query.index(">"):
                raise Exception("Invalid XML tags")

        # Check for invalid characters
        invalid_characters = ["\n", "\r", "\t"]
        for invalid_character in invalid_characters:
            if invalid_character in query:
                raise Exception("Invalid characters")

        # Check for invalid words
        invalid_words = ["<出力>", "</出力>", "<発言>", "</発言>"]
        for invalid_word in invalid_words:
            if invalid_word in query:
                raise Exception("Invalid words")

    async def CheckResponseText(self, text: str) -> None:

        # Valid text format:
        # <出力><発言>This is the response message</発言></出力>

        # Check if the text is valid
        if not text:
            raise Exception("Text is empty")

        # Check if the text is in the valid format
        if "<出力>" not in text or "</出力>" not in text:
            raise Exception("Invalid text format")

        # Check if the text is in the valid format
        if "<発言>" not in text or "</発言>" not in text:
            raise Exception("Invalid text format")


async def setup(bot):
    await bot.add_cog(Chat(bot))
