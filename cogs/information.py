import json
import math
import platform

import discord
import psutil
from discord import Embed
from discord.ext import commands
from discord.commands import slash_command

from .functions import PageButtons, response


class information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("information.py Loaded!")

    @slash_command(name="help", description="Learn about my commands")
    async def help(self, ctx, command: discord.Option(str, description="The command you want to see more info about", required=False, choices=[x for x in dict(sorted(json.load(open("./json/help.json", "r")).items(), key=lambda x: x[0]))])): # type: ignore
        if command != None:
            docs_link = f"https://docs.{self.bot.website.replace('https://', '')}/commands/{command}"
            await ctx.respond(embed=discord.Embed(title=f"/{command} info", description=f"**Description**\n{self.bot.helpinfo[command]['desc_long']}\n\n **Doccumentation**\n [{docs_link.replace('https://', '')}]({docs_link})", colour=self.bot.Blue))
            return

        async def embed(page, maxpage, bot_commands):
            description = f"{self.bot.bot_emojis['pulsing_dot']}To access additional resources, visit [{self.bot.website.replace('https://', '')}]({self.bot.website})\n"
            description += f"{self.bot.bot_emojis['pulsing_dot']}For one on one assistance join the [support server]({self.bot.supportserver}).\n"

            for x in bot_commands[((page*8) - 8):(page*8)]:
                found = False
                for command in self.bot.walk_application_commands():
                    if command.name == x:
                        description += f"\n{command.mention}\n{self.bot.bot_emojis['reply']}{self.bot.helpinfo[x]['desc_short']}"
                        found = True
                        break
                if not found:
                    description += f"\n/{x}\n{self.bot.bot_emojis['reply']}{self.bot.helpinfo[x]['desc_short']}"

            em = discord.Embed(description=description, colour=self.bot.Blue)
            em.set_footer(text=f"Page {page}/{maxpage}")
            return em
        bot_commands = [x for x in self.bot.helpinfo]
        await PageButtons(self.bot, ctx, True, "reply", embed, 1, math.ceil(len(bot_commands)/8), 10, bot_commands).start()

    @slash_command(name="botinfo", description=json.load(open("./json/help.json", "r"))["botinfo"]['desc_short'])
    async def botinfo(self, ctx):
        bot_emojis = self.bot.bot_emojis

        memory_total = psutil.virtual_memory()._asdict()["total"]
        memory_used = psutil.virtual_memory()._asdict()["used"]
        cpu_percent = psutil.cpu_percent()

        Host = [f"**OS**: `{platform.system()} ({platform.release()})`",
                f"**Library**: `Pycord {discord.__version__}`",
                f"**Memory Usage**: `{round(memory_used/1000000000, 1)}/{round(memory_total/1000000000, 1)}GB`",
                f"**CPU Usage**: `{cpu_percent}%`"]

        Stats = [f"**Guilds**: `{len(self.bot.guilds)}`",
                 f"**Users**: `{sum(len([m for m in x.members if not m.bot]) for x in self.bot.guilds)}`",
                 f"**Shard Count**: `{self.bot.shard_count}`"]

        shard_id = ctx.guild.shard_id
        shard = self.bot.get_shard(shard_id)

        Shard = [f"**Guilds**: `{len([guild for guild in self.bot.guilds if guild.shard_id == shard_id])}`",
                 f"**Users**: `{sum(len([m for m in guild.members if not m.bot]) for guild in self.bot.guilds if guild.shard_id == shard_id)}`",
                 f"**Ping**: `{round(shard.latency * 1000)}ms`"]

        Links = [f"**Invite me:** [admin_perms](https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands)",
                 f"**Support Server:** {self.bot.supportserver}",
                 f"**Website:** {self.bot.website}"]

        em = Embed(title=f"Bot Information - {self.bot.user}",
                   description=f'{self.bot.user.name} is an advanced counting bot that can manage a counting channel in your guild. With a simple setup, your channel is ready.',
                   colour=self.bot.Blue)

        em.add_field(name=f"{bot_emojis['folder']} Host", value=f"{Host[0]}\n{Host[1]}\n{Host[2]}\n{Host[3]}", inline=True)
        em.add_field(name=f"{bot_emojis['stats']} Stats", value=f"{Stats[0]}\n{Stats[1]}\n{Stats[2]}", inline=True)
        em.add_field(name=f"{bot_emojis['shard']} This Shard ({shard_id})", value=f"{Shard[0]}\n{Shard[1]}\n{Shard[2]}", inline=True)
        em.add_field(name=f"{bot_emojis['link']} Links", value=f"{Links[0]}\n{Links[1]}\n{Links[2]}", inline=False)

        await ctx.respond(embed=em)

    @slash_command(name="vote", description=json.load(open("./json/help.json", "r"))["vote"]['desc_short'])
    async def vote(self, ctx):
        em = discord.Embed(title=f"Vote for {self.bot.user.name}",
                           description="",
                           colour=self.bot.Blue)
        em.set_thumbnail(url="https://i.imgur.com/ahygnwR.png")
        em.add_field(name="**Reward**", value=f"` - ` 50x {self.bot.bot_emojis['coins']} Coins", inline=False)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='top.gg', url=f'https://top.gg/bot/{self.bot.user.id}/vote', style=discord.ButtonStyle.url))
        view.add_item(discord.ui.Button(label='discordbotlist.com', url=f'https://discordbotlist.com/bots/counter-2119/upvote', style=discord.ButtonStyle.url))

        await ctx.respond(embed=em, view=view)
    
    class mydataView(discord.ui.View):
        def __init__(self, bot, ctx, timeout, *args, **kwargs):
            super().__init__(timeout=timeout)
            self.bot = bot
            self.ctx = ctx
            self.data_delete_type = "null"
            self.args = args
            self.kwargs = kwargs
        
        @discord.ui.button(label='User', style=discord.ButtonStyle.primary)
        async def user(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.data_delete_type = "user"
            # remove all buttons
            for button in reversed(self.children):
                self.remove_item(button)
                
            # get user data
            cluster = self.bot.mongodb["Counting"]["User"]
            user_data = cluster.find_one({"userId": self.ctx.author.id})
            if user_data is None:
                em = discord.Embed(description=f"{self.bot.bot_emojis['info']} User has no Data.", colour=self.bot.Blue)
                await interaction.response.edit_message(embed=em, view=self)
                return
            
            # add delete button
            self.add_item(self.delete)
            
            # are you sure?
            em = discord.Embed(description=f"{self.bot.bot_emojis['danger']} Are you sure you want to delete your user data?\n This action is irreversible!", colour=self.bot.Red)
            await interaction.response.edit_message(embed=em, view=self)
            
        @discord.ui.button(label='Guild', style=discord.ButtonStyle.primary)
        async def guild(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.data_delete_type = "guild"
            # remove all buttons
            for button in reversed(self.children):
                self.remove_item(button)
            
            # check if user is admin in guild
            if not self.ctx.author.guild_permissions.administrator:
                em = discord.Embed(description=f"{self.bot.bot_emojis['danger']} You are missing the permission `administrator`.", colour=self.bot.Red)
                await interaction.response.edit_message(embed=em, view=self)
                return
            
            # get guild data
            cluster = self.bot.mongodb["Counting"]["Guild"]
            guild_data = cluster.find_one({"guildId": self.ctx.guild.id})
            if guild_data is None:
                em = discord.Embed(description=f"{self.bot.bot_emojis['info']} Guild has no Data.", colour=self.bot.Blue)
                await interaction.response.edit_message(embed=em, view=self)
                return
                
            # add delete button
            self.add_item(self.delete)
                
            # are you sure?
            em = discord.Embed(description=f"{self.bot.bot_emojis['danger']} Are you sure you want to delete this guilds data?\n This action is irreversible!", colour=self.bot.Red)
            await interaction.response.edit_message(embed=em, view=self)
             
        @discord.ui.button(label='Delete', style=discord.ButtonStyle.danger)
        async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.disable_all_items()
            if self.data_delete_type == "null":
                return
            
            if self.data_delete_type == "user":
                cluster = self.bot.mongodb["Counting"]["User"]
                cluster.delete_one({"userId": self.ctx.author.id})
                em = discord.Embed(description=f"{self.bot.bot_emojis['green_check']} User data deleted.", colour=self.bot.Green)
                await interaction.response.edit_message(embed=em, view=self)
                return
            
            if self.data_delete_type == "guild":
                cluster = self.bot.mongodb["Counting"]["Guild"]
                cluster.delete_one({"guildId": self.ctx.guild.id})
                em = discord.Embed(description=f"{self.bot.bot_emojis['green_check']} Guild data deleted.", colour=self.bot.Green)
                await interaction.response.edit_message(embed=em, view=self)
                return
            
        async def on_timeout(self):
            self.disable_all_items()
            await response(True, "edit", self.message, view=self)
            
        async def start(self):
            self.remove_item(self.delete)
            
            em = discord.Embed(title=f"My Data - {self.ctx.author}", description=f"Select the data type to delete.", colour=self.bot.Blue)
            self.message = await response(True, "reply", self.ctx, embed=em, view=self, ephemeral=True)
    
    @slash_command(name="deletedata", description=json.load(open("./json/help.json", "r"))["deletedata"]['desc_short'])
    async def deletedata(self, ctx):
        await self.mydataView(self.bot, ctx, 10).start()
        
#####################################################################################################################################


def setup(bot):
    bot.add_cog(information(bot))
