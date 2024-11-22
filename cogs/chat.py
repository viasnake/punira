import discord
import requests
from discord.ext import commands
from discord.ext.commands import Context

class Chat(commands.Cog, name="Chat"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def chat(self, context: Context) -> None:
        """
        The code in this event is executed every time the bot detects a message.

        :param context: The context of the message that has been sent.
        """
        # チャンネル名に指定された文字列で始まっていない場合、無視する
        ALLOWED_CHANNEL_NAMES = ["punira"]
        if not any(
            context.channel.name.startswith(channel_name)
            for channel_name in ALLOWED_CHANNEL_NAMES
        ):
            return

        # 自分に対するメンション以外は無視する
        if not context.mentions:
            return

        # Bot からのメッセージの場合、無視する
        if context.author.bot:
            return

        # 画像が含まれるメッセージの場合、無視する
        if context.attachments:
            return

        # メンションが含まれていたら、表示名に置き換える
        for mention in context.mentions:
            context.content = context.content.replace(
                f"<@{mention.id}>", mention.display_name
            )

        # 文字数が多い場合、無視する
        if len(context.content) > 300:
            return

        # メッセージを送信したユーザーの名前を取得する
        user = context.author.display_name

        # メッセージの内容を取得する
        query = context.content

        # チャンネル ID を取得する
        channel_id = str(context.channel.id)

        # メッセージの内容を送信して、返答を取得する
        response = await GetResponse(self.bot, query, user, channel_id)

        # 返答が空の場合、無視する
        if not response:
            return

        # 返答を送信する
        await context.reply(response)


async def GetResponse(bot, query: str, user: str, channel_id: str) -> str:

    # 会話 ID を取得する
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

    response = requests.post(
        API_URL,
        headers=headers,
        json=data,
    )

    # 会話 ID が存在しない場合、会話 ID を保存する
    if not conversation_id:
        await SaveConversationId(channel_id, response.json()["conversation_id"])

    return response.json()["answer"]

async def SaveConversationId(channel_id: str, conversation_id: str) -> None:
    # ファイルが存在しない場合、作成する
    with open("conversation_id.txt", "a") as file:
        pass

    # ファイルに会話 ID を追記する
    # 会話 ID は以下の形式で保存する
    # チャンネル ID:会話 ID
    with open("conversation_id.txt", "a") as file:
        file.write(f"{channel_id}:{conversation_id}\n")

async def GetConversationId(channel_id: str) -> str:
    conversation_id = ""

    # ファイルから会話 ID を取得する
    # 会話 ID は以下の形式で保存されている
    # チャンネル ID:会話 ID
    with open("conversation_id.txt", "r") as file:
        for line in file:
            temp_channel_id, temp_conversation_id = line.split(":")

            # チャンネル ID が一致する場合、会話 ID を返す
            if channel_id == temp_channel_id:
                conversation_id = temp_conversation_id

    # 改行文字を削除する
    conversation_id = conversation_id.rstrip("\n")

    return conversation_id

async def setup(bot):
    await bot.add_cog(Chat(bot))
