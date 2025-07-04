import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from pymongo import MongoClient
import os
import json
import discord
from discord.ext import commands
from pymongo import MongoClient

class Bot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix="c!",
                         case_insensitive=True,
                         # shard_count=2,
                         intents=discord.Intents.default() | discord.Intents(message_content=True),
                         activity=discord.Streaming(name="/help", url="https://www.twitch.tv/counter_discordbot"))
        self.remove_command('help')

        botishosted = False
        if botishosted == True:
            self.Secrets = json.loads(os.environ.get('Secrets'))
        else:
            with open("./json/Secrets.json", "r") as f:
                self.Secrets = json.load(f)

        self.owner_id = 1139476252890255452
        self.website = "https://counterbot.app"
        self.supportserver = "https://counterbot.app/support"

        self.testbot_id = 1008308819983597608
        self.errors_channel = 1386927530518249616

        self.mongodb = MongoClient(self.Secrets["MongoClientLink"])

        self.Yellow = int("FFB744", 16)
        self.Black = int("000000", 16)
        self.Green = int("2EC550", 16)
        self.Red = int("D72D42", 16)
        self.Blue = int("7289DA", 16)

        # help info
        with open("./json/help.json", "r") as f:
            self.helpinfo = json.load(f)
            self.helpinfo = dict(
                sorted(self.helpinfo.items(), key=lambda x: x[0]))

        # bot emojis
        with open("./json/emojis.json", "r") as f:
            self.bot_emojis = json.load(f)

        # fonts
        with open("./json/fonts.json", "r") as f:
            self.fonts = json.load(f)

        # load cogs
        for filename in os.listdir('cogs'):
            if filename.endswith('.py'):
                if filename != "functions.py":
                    if filename != "vote.py":
                        self.load_extension(f'cogs.{filename[:-3]}')

    async def on_application_command_error(self, ctx, error):
        channel = self.get_channel(self.errors_channel)
        # prevent reports from testing bot
        if self.user.id == self.testbot_id:
            raise error

        em = discord.Embed(
            title="Error", description=f"**Command:** {ctx.command}```{error}```", color=self.Red)

        if ctx.guild:
            origin = f"**Guild:** {ctx.guild.name} ` - ` **Guild id:** {ctx.guild.id}"
            origin += f"\n**Channel:** {ctx.channel.mention} ` - ` **Channel id:** {ctx.channel.id}"
        else:
            origin = f"**Channel:** Bot's DM ` - ` **Channel id:** {ctx.channel.id}"

        origin += f"\n**User:** {ctx.author.mention} ` - ` **User id:** {ctx.author.id}"

        em.add_field(name="🛰️Origin", value=f"{origin}", inline=False)
        await channel.send(embed=em)
        raise error

    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return

    async def on_ready(self):
        print('Logged in as')
        print('Name:', self.user.name)
        print('ID:', self.user.id)
        print('------')
        print('main.py Loaded!')

    async def on_connect(self):
        print("Bot has connected")
        await self.sync_commands()

    async def on_disconnect(self):
        print("Bot has disconnected")


if __name__ == "__main__":
    client = Bot()
#####################################################################################################################################
client.run(client.Secrets["Token"])
