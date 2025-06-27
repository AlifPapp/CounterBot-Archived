import asyncio
import random
import string
import datetime
import math

import discord
from discord.ext import commands

from datetime import datetime
from discord import Permissions

from cogs.counting import convert_num2emoji

from .functions import PageButtons, get_webhook


class creator_cmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("creator_cmds.py Loaded!")

    async def cog_check(self, ctx):
        try:
            if ctx.author.id == self.bot.owner_id or ctx.author.id == 1357302891110600754:
                return True
        except:
            pass
    
    # c!serveremojis
    @commands.command(aliases=["se"])
    async def serveremojis(self, ctx, page: int = 1):
        try: 
            page = abs(int(page)) 
            if page < 1: 
                page = 1
        except: 
            page = 1
        
        if len(ctx.guild.emojis) == 0:
            await ctx.send(embed=discord.Embed(description="Server has no emojis!", color=self.bot.Red))
            return

        maxpage = math.ceil(len(ctx.guild.emojis)/10)
        if page > maxpage:
            page = maxpage
        
        async def embed(page, maxpage):
            em = discord.Embed(color=self.bot.Blue)
            emojis_list = ""
            cycle = 0
            for e in ctx.guild.emojis:
                cycle = cycle + 1
                if cycle > ((page*10) - 10) or page == 1:
                    if e.animated:
                        emojis_list += f"**{cycle}** - 『{e}』－`<a:{e.name}:{e.id}>`\n"
                    else:
                        emojis_list += f"**{cycle}** - 『{e}』－`<:{e.name}:{e.id}>`\n"
                if cycle == int(page*10):
                    break
            em.add_field(name=f"Emojis [{len(ctx.guild.emojis)}]", value=emojis_list)
            em.set_footer(text=f"Page: {page}/{maxpage}")
            return em
        await PageButtons(self.bot, ctx, False, "send", embed, page, maxpage, 10).start()

    # c!botemojis
    @commands.command(aliases=["be"])
    async def botemojis(self, ctx, page: int = 1):
        bot_emojis = self.bot.bot_emojis
        
        try: 
            page = abs(int(page)) 
            if page < 1: 
                page = 1
        except: 
            page = 1

        maxpage = math.ceil(len(bot_emojis)/10)
        if page > maxpage:
            page = maxpage
        async def embed(page, maxpage):
            em = discord.Embed(color=self.bot.Blue)
            emojis_list = ""
            cycle = 0
            for e in bot_emojis:
                cycle = cycle + 1
                if cycle > ((page*10) - 10) or page == 1:
                    emojis_list += f"**{cycle}** - 『{bot_emojis[e]}』－`{bot_emojis[e]}`\n"
                if cycle == int(page*10):
                    break
            em.add_field(name=f"Emojis [{len(bot_emojis)}]", value=emojis_list)
            em.set_footer(text=f"Page: {page}/{maxpage}")
            return em
        await PageButtons(self.bot, ctx, False, "send", embed, page, maxpage, 10).start()

    # tdevpurge <ammount>
    @commands.command()
    async def devpurge(self, ctx, l: int = 50):
        if ctx.guild is not None:
            await ctx.message.delete()
            c = await ctx.channel.purge(limit=l)
            await ctx.send(f"Cleared {len(c)} messages", delete_after=3)
        else:
            messages = await ctx.channel.history(limit=l).flatten()
            c = 0
            for msg in messages:
                if msg.author.id == self.bot.user.id:
                    await msg.delete()
                    await asyncio.sleep(0.5)
                    c = c + 1
            await ctx.send(f"Cleared {c} messages", delete_after=3)

    # c!shutdown
    @commands.command()
    async def shutdown(self, ctx):
        if ctx.guild is None:
            await ctx.send('Shutting down...')
            exit()

    # c!listservers
    @commands.command()
    async def listservers(self, ctx):
        if ctx.guild is None: 
            activeservers = self.bot.guilds
            serverlist = ""
            acceptedchars = ["'","!","?"]
            for guild in activeservers:
                guildname_checked = " "
                for i in guild.name:
                    if i in string.ascii_letters or i.isspace() or i in acceptedchars:
                        guildname_checked += i
                    else:
                        guildname_checked += "_"
                serverlist += f"Name: {guildname_checked}, MemberCount: {guild.member_count}, GuildID: {guild.id}\n"

            with open("result.txt", "w") as file:
                file.write(serverlist)
            
            # send file to Discord in message
            with open("result.txt", "rb") as file:
                await ctx.reply("**guild names** only shown in characters `a-z`.\n**Unsupported** characters are displayed as `_`\noutput:", file=discord.File(file, "result.txt"))

    # c!serverinvite <id> 
    @commands.command()
    async def serverinvite(self, ctx, target: int=0):
        if ctx.guild is None: 
            targetguild = self.bot.get_guild(target)
            link = await targetguild.text_channels[0].create_invite(max_age = 0, max_uses=0)
            await ctx.send(f"Invite for {targetguild.name}: {link}")

    # c!embedcolortest <color>
    @commands.command()
    async def embedcolortest(self, ctx, colortest: str="002240"):
        if "#" in colortest:
            colortest = colortest.replace("#", "")
        readableHex = int(colortest, 16)

        em = discord.Embed(title = "Embed Color Test",
                           description = f"Testing: {colortest}\nDefault Color: `#002240`",
                           color = readableHex,
                           timestamp=datetime.utcnow())

        await ctx.send(embed = em)

    # c!simulate
    @commands.command()
    async def simulate(self, ctx):
        await ctx.send("Simulating...")
        
        bot_emojis = self.bot.bot_emojis
        
        # range
        start = 49
        end = 100
        
        # channel
        channel = self.bot.get_channel(1207258716991262780)
        
        # users
        usernames = ["User", "User 2", "User 3"]
        avatar_urls = [
            "https://cdn.discordapp.com/attachments/1052777220537589782/1207260087392145469/discord-logo-icon-editorial-free-vector.jpg", 
            "https://cdn.discordapp.com/attachments/1052777220537589782/1207260087014391808/4205-orange-discord-pfp.png",
            "https://cdn.discordapp.com/attachments/1052777220537589782/1207260086750289941/3c6ccb83716d1e4fb91d3082f6b21d77.png"
            ]
        mentions = ["<@!1166281470860611605>", "<@!1008308701033152553>", "<@!270904126974590976>"]
        bot_avatar_url = "https://cdn.discordapp.com/avatars/1207908815551594518/4061a919d7be17374e9797a5faf8c144.png"
        
        tugofwar_speech = ["Tug of War!",
                           "Stop counting down!",
                            "Stop counting up!",
                            "We must reach 100!",
                            "HAHA! we will stop you!",
                            
                            "Noooo!",
                            "#countdown",
                            "#countup",
                            "We will win!",
                            "WTF!?",
                            
                            "LMAO!"
                           ]
        
        nofails_speech = ["No fails!",
                          "Don't you mess it up!",
                          "How can you fail at counting?",
                          "Are you even trying?",
                          "Are you stupid?"
                        ]
        
        nofails_speech2 = ["Don't you mess it up!",
                           "Don't you dare!",
                           "Keep it up!",
                           "We can do it!"]
        
        # tug of war
        if 1 == 0:
            temp_number = start
            for i in range(start, end):
                type = "up"
                
                # choose random tugofwar_speech
                speech = random.randint(0, len(tugofwar_speech) - 1)
                
                # select type based on speech
                if speech == 0:
                    type = "up"
                if speech == 1:
                    type = "up"
                if speech == 2:
                    type = "down"
                if speech == 3:
                    type = "up"
                if speech == 4:
                    type = "down"
                    
                if speech == 5:
                    type = "down"
                if speech == 6:
                    type = "down"
                if speech == 7:
                    type = "up"
                if speech == 8:
                    type = "down"
                if speech == 9:
                    type = "down"
                
                if speech == 10:
                    type = "up"
                
                    
                # calculate number
                if type == "up":
                    number = temp_number + 1
                if type == "down":
                    number = temp_number - 1
                temp_number = number # save for next loop
                
                # random number beetween 1 and 18
                font_id = random.randint(1, 18)

                username = usernames[i % 3]
                avatar_url = avatar_urls[i % 3]
            
                # Find webhook
                webhook = await get_webhook(self, ctx)
                
                text = f' {tugofwar_speech[speech]}'
                
                # 33% chance of text being empty
                if random.randint(1, 3) == 1:
                    text = ""
            
                # Send webhook
                await webhook.send(content=f'{convert_num2emoji(self, number, font_id)}{text}', username=username, avatar_url=avatar_url)
            
                # sleep
                await asyncio.sleep(1)
            
                print(f"Sent {number}")
        
        # no fails
        if 1 == 1:
            await ctx.send("Simulating no fails")
            temp_number = start
            failed = False
            for i in range(start, end):
                number = temp_number + 1
                fail = False
                
                # 20 % chance of fail
                if random.randint(1, 5) == 1:
                    fail = True
                    t = random.randint(0, 2)
                    if t == 0:
                        number = temp_number + 1
                    elif t == 1:
                        number = temp_number - 1
                    elif t == 2:
                        number = temp_number + 2
                    
                if failed == True:
                    fail = False
                    number = temp_number + 1
                    
                username = usernames[i % 3]
                avatar_url = avatar_urls[i % 3]
                mention = mentions[i % 3]
                
                # random number beetween 1 and 18
                font_id = 1 + (i % 18)
                
                # Find webhook
                webhook = await get_webhook(self, ctx)
                if fail == True:
                    #send webhook
                    await webhook.send(content=f'{convert_num2emoji(self, number, font_id)}', username=username, avatar_url=avatar_url)
                    
                    # Send webhook
                    await webhook.send(embed=discord.Embed(description=f'{bot_emojis["danger"]} {mention} Ruined it at **{temp_number}**! Next number is **1**.', color=self.bot.Red), username=f"{self.bot.user.display_name}", avatar_url=bot_avatar_url)
                    
                    # save for next loop
                    temp_number = 0 
                    failed = True
                else:
                    number = temp_number + 1
                    
                    text = f' {nofails_speech2[i % 4]}' # encourage speech
                    
                    # 50% chance of text being empty
                    if random.randint(1, 2) == 1:
                        text = "" # no speech
                    
                    if failed == True:
                        text = f' {nofails_speech[i % 5]}' # angry speech
                    failed = False # reset
                    
                    #send webhook
                    await webhook.send(content=f'{convert_num2emoji(self, number, font_id)}{text}', username=username, avatar_url=avatar_url)
                    
                    # save for next loop
                    temp_number = number
                # sleep
                await asyncio.sleep(1)
            
                print(f"Sent {number}")
                
        # normal count up
        if 1 == 0:
            for i in range(start, end):
                number = i
            
                # random number beetween 1 and 18
                font_id = 1 + (i % 18)
            
                username = usernames[i % 3]
                avatar_url = avatar_urls[i % 3]
            
                # Find webhook
                webhook = await get_webhook(self, ctx)
            
                # Send webhook
                await webhook.send(content=f'{convert_num2emoji(self, number, font_id)}', username=username, avatar_url=avatar_url)
            
                # sleep
                await asyncio.sleep(1)
            
                print(f"Sent {number}")
        
        await ctx.send("Simulation complete.")

#####################################################################################################################################

def setup(bot):
    bot.add_cog(creator_cmds(bot))
