import json
import math
import random
from typing import Optional
import discord
from discord import Member
from discord.ext import commands
from discord.commands import slash_command
from aiohttp import web
import hmac, hashlib
from .functions import Dropdown, PageButtons, get_webhook, user_avatar_url


class counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("counting.py Loaded!")

    @commands.Cog.listener()
    async def on_message(self, ctx):
        # Check if message is in a guild
        if ctx.guild is None:
            return

        # Check if message is webhook
        user = ctx.author
        if user.bot:  # So dont always have to search through list
            # Filter out webhook from actualy bots
            if user not in list(filter(lambda m: m.bot, ctx.guild.members)):
                return

        # Setup Vars
        guild = ctx.guild
        channel = ctx.channel
        cluster = self.bot.mongodb["Counting"]["Guild"]
        fonts = self.bot.fonts
        bot_emojis = self.bot.bot_emojis

        # Check if guild is in database
        guild_data = cluster.find_one({"guildId": guild.id})
        if guild_data is None:
            return

        # Check if channel is in database
        try:
            channel_data = guild_data["channels"][str(channel.id)]
        except KeyError:
            return

        # await asyncio.sleep(0.25)  # delay for message delete

        # Check if user was previous user
        if channel_data["alternate"] == True:
            if channel_data["lastUser"] == user.id:
                await ctx.delete()
                # Check if fails mode is enabled
                if channel_data["gamemode"] == "No Fails":
                    # Send webhook
                    webhook = await get_webhook(self, ctx)
                    await webhook.send(embed=discord.Embed(description=f'{bot_emojis["danger"]} {user.mention} Ruined it at **{channel_data["number"]}**! Next number is **{channel_data["startingNumber"] + channel_data["interval"]}**.', color=self.bot.Red), username=f"{self.bot.user.display_name}", avatar_url=user_avatar_url(self.bot.user))
                    # Reset number
                    guild_data["channels"][str(
                        channel.id)]["number"] = channel_data["startingNumber"]
                    # update database
                    cluster.update_one({"guildId": guild.id}, {
                                       "$set": {"channels": guild_data["channels"]}})
                    return
                return

        # array of valid numbers for channel
        valid_numbers = [channel_data["number"] + channel_data["interval"]]
        if channel_data["gamemode"] == "Tug Of War":
            valid_numbers.append(
                channel_data["number"] - channel_data["interval"])

        # Check if start of message is a valid number
        valid_number = False
        for x in valid_numbers:
            if str(ctx.content).startswith(str(x)):
                valid_number = x
                break

        # Not a valid number
        if valid_number == False:
            # Check if fails mode is enabled
            if channel_data["gamemode"] == "No Fails":
                # Send webhook
                webhook = await get_webhook(self, ctx)
                await webhook.send(embed=discord.Embed(description=f'{bot_emojis["danger"]} {user.mention} Ruined it at **{channel_data["number"]}**! Next number is **{channel_data["startingNumber"] + channel_data["interval"]}**.', color=self.bot.Red), username=f"{self.bot.user.display_name}", avatar_url=user_avatar_url(self.bot.user))
                # Reset number
                guild_data["channels"][str(
                    channel.id)]["number"] = channel_data["startingNumber"]
                # update database
                cluster.update_one({"guildId": guild.id}, {
                    "$set": {"channels": guild_data["channels"]}})
                return
            else:
                await ctx.delete()
                return

        # Check if it contains text
        if channel_data["talking"] == False:
            if ctx.content != str(valid_number):
                await ctx.delete()
                return

        # Get values for user
        cluster_user = self.bot.mongodb["Counting"]["User"]
        user_data = cluster_user.find_one({"userId": user.id})
        if user_data is None:
            user_data = new_user_data(user.id)
            cluster_user.insert_one(user_data)

        # if equipped font doesnt exist, set to default
        if str(user_data["equippedFontId"]) not in fonts:
            user_data["equippedFontId"] = 0
            cluster_user.update_one({"userId": user.id}, {
                "$set": {"equippedFontId": 0}})

        # Delete original message
        await ctx.delete()

        # Find webhook
        webhook = await get_webhook(self, ctx)
        # split content
        if len(str(valid_number)) == len(ctx.content):
            content = ""
        else:
            content = f" {ctx.content[len(str(valid_number))::].lstrip()}"
            if (len(str(valid_number)) + len(ctx.content)) > 2000:
                # cut off end of message
                content = f" {ctx.content[len(str(valid_number)):(2000 - len(str(valid_number)))].lstrip()}"
        # Send webhook
        if channel_data["fontsEnabled"] == True:
            await webhook.send(content=f'{convert_num2emoji(self, valid_number, user_data["equippedFontId"])}{content}', username=f"{ctx.author.display_name}", avatar_url=user_avatar_url(user))
        else:
            await webhook.send(content=f'{valid_number}{content}', username=f"{ctx.author.display_name}", avatar_url=user_avatar_url(user))

        # Update database for guild
        guild_data["channels"][str(channel.id)]["number"] = valid_number
        guild_data["channels"][str(channel.id)]["lastUser"] = user.id
        cluster.update_one({"guildId": guild.id}, {
            "$set": {"channels": guild_data["channels"]}})

        # Update database for user
        user_data["coins"] += 1
        user_data["totalCounted"] += 1
        if channel_data["fontsEnabled"] == True:
            user_data["fonts"][str(
                user_data["equippedFontId"])]["totalCounted"] += 1
        else:
            user_data["fonts"]["0"]["totalCounted"] += 1
        cluster_user.update_one({"userId": user.id}, {
            "$set": {"coins": user_data["coins"], "totalCounted": user_data["totalCounted"], "fonts": user_data["fonts"]}})

    @slash_command(name="setup", description=json.load(open("./json/help.json", "r"))["setup"]['desc_short'])
    async def setup(self, ctx: discord.ApplicationContext,
                    channel: discord.TextChannel,
                    number: discord.Option(int),  # type: ignore
                    interval: discord.Option(int),  # type: ignore
                    alternate: discord.Option(bool),  # type: ignore
                    fonts: discord.Option(bool),  # type: ignore
                    talking: discord.Option(bool),  # type: ignore
                    # type: ignore
                    gamemode: discord.Option(str, choices=['False', 'Tug Of War', 'No Fails'])):

        # Check if user has permission
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond(embed=discord.Embed(
                title=f"",
                description=f"{self.bot.bot_emojis['danger']} You are missing the permission `administrator`.",
                colour=self.bot.Red))
            return

        # Setup Vars
        guild = ctx.guild
        user = ctx.author
        cluster = self.bot.mongodb["Counting"]["Guild"]
        bot_emojis = self.bot.bot_emojis

        # Check if channel is already setup
        guild_data = cluster.find_one({"guildId": guild.id})
        if guild_data is not None:
            if str(channel.id) in guild_data["channels"]:
                await ctx.respond(embed=discord.Embed(
                    title=f"",
                    description=f"{bot_emojis['danger']} This channel is already setup.",
                    colour=self.bot.Red))
                return
        else:
            guild_data = new_guild_data(guild.id)
            cluster.insert_one(guild_data)

        # add channel setup to database
        guild_data["channels"][str(channel.id)] = {
            "number": number,
            "startingNumber": number,
            "interval": interval,
            "alternate": alternate,
            "lastUser": user.id,
            "talking": talking,
            "fontsEnabled": fonts,
            "gamemode": gamemode
        }

        # update database
        cluster.update_one({"guildId": guild.id}, {
                           "$set": {"channels": guild_data["channels"]}})

        # Send embed
        description = f"{bot_emojis['green_check']} Setup Complete.\n \n"
        description += f"{bot_emojis['marked_checkbox']} **[Channel:]({self.bot.website})** {channel.mention}\n"
        description += f"{bot_emojis['marked_checkbox']} **[Starting number:]({self.bot.website})** {number}\n"
        description += f"{bot_emojis['marked_checkbox']} **[Interval:]({self.bot.website})** {interval}\n"
        description += f"{bot_emojis['marked_checkbox']} **[Alternate:]({self.bot.website})** {alternate}\n"
        description += f"{bot_emojis['marked_checkbox']} **[Fonts:]({self.bot.website})** {fonts}\n"
        description += f"{bot_emojis['marked_checkbox']} **[Talking:]({self.bot.website})** {talking}\n"
        description += f"{bot_emojis['marked_checkbox']} **[GameMode:]({self.bot.website})** {gamemode}\n"

        em = discord.Embed(title=f"",
                           description=description,
                           colour=self.bot.Green)
        await ctx.respond(embed=em)

    @slash_command(name="disable", description=json.load(open("./json/help.json", "r"))["disable"]['desc_short'])
    async def disable(self, ctx: discord.ApplicationContext):
        # Check if user has permission
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond(embed=discord.Embed(
                title=f"",
                description=f"{self.bot.bot_emojis['danger']} You are missing the permission `administrator`.",
                colour=self.bot.Red))
            return

        # Setup Vars
        guild = ctx.guild
        cluster = self.bot.mongodb["Counting"]["Guild"]
        bot_emojis = self.bot.bot_emojis

        # find guild data
        guild_data = cluster.find_one({"guildId": guild.id})
        if guild_data is None:
            guild_data = new_guild_data(guild.id)

        # EMBED FUNCTION
        async def embed(id):
            # intial message
            if id == 0:
                # Select a channel
                return discord.Embed(description=f"{self.bot.bot_emojis['info']} Select a channel to disable.", colour=self.bot.Blue)

            description = f""
            for x in id:
                # remove channel from database
                del guild_data["channels"][str(x)]
                # add to list
                description += f"{bot_emojis['green_check']} Disabled <#{x}>\n"

            # update database
            cluster.update_one({"guildId": guild.id}, {
                "$set": {"channels": guild_data["channels"]}})

            return discord.Embed(description=description, color=self.bot.Green)

        # Options
        options = []
        for x in guild_data["channels"]:
            options.append(discord.SelectOption(
                label=f"# {guild.get_channel(int(x)).name}", value=x))

        # if no channels setup
        max_values = len(options)
        if max_values == 0:
            await ctx.respond(embed=discord.Embed(description=f"{bot_emojis['danger']} There are no counting channels to disable.", colour=self.bot.Red))
            return

        if max_values > 9:
            max_values = 9
        await Dropdown(self.bot, ctx, True, "reply", embed, "Select a channel", 1, int(max_values), options, 10).start()

    @slash_command(name="channel", description=json.load(open("./json/help.json", "r"))["channel"]['desc_short'])
    async def channel(self, ctx: discord.ApplicationContext):
        # Setup Vars
        guild = ctx.guild
        cluster = self.bot.mongodb["Counting"]["Guild"]
        bot_emojis = self.bot.bot_emojis

        # find guild data
        guild_data = cluster.find_one({"guildId": guild.id})
        if guild_data is None:
            guild_data = new_guild_data(guild.id)

        # Delete channel setup that cant be found in guild
        new_guid_data = {}
        for x in guild_data["channels"]:
            if guild.get_channel(int(x)):
                new_guid_data[x] = guild_data["channels"][x]
        guild_data["channels"] = new_guid_data

        # update database
        cluster.update_one({"guildId": guild.id}, {
            "$set": {"channels": guild_data["channels"]}})

        # see if there are any channel in database
        if len(guild_data["channels"]) == 0:
            await ctx.respond(embed=discord.Embed(description=f"{bot_emojis['danger']} There are no counting channels.", colour=self.bot.Red))
            return

        # EMBED FUNCTION
        async def embed(id):
            # intial message
            if id == 0:
                # Select a channel
                return discord.Embed(description=f"{self.bot.bot_emojis['info']} Select a channel to view its info.", colour=self.bot.Blue)

            # keep only first value of list since can only select one
            id = id[0]

            # display channel info
            if str(id) not in guild_data["channels"]:
                return discord.Embed(description=f"{self.bot.bot_emojis['danger']} This is not a counting channel.", colour=self.bot.Red)
            info = guild_data['channels'][str(id)]
            description = f"{bot_emojis['static_cog']} **Channel Info**\n \n"
            description += f"<#{id}>\n"
            description += f"{bot_emojis['marked_checkbox']} **[Current number:]({self.bot.website})** {str(info['number']).capitalize()}\n"
            description += f"{bot_emojis['marked_checkbox']} **[Interval:]({self.bot.website})** {str(info['interval']).capitalize()}\n"
            description += f"{bot_emojis['marked_checkbox']} **[Alternate:]({self.bot.website})** {str(info['alternate']).capitalize()}\n"
            description += f"{bot_emojis['marked_checkbox']} **[Fonts:]({self.bot.website})** {str(info['fontsEnabled']).capitalize()}\n"
            description += f"{bot_emojis['marked_checkbox']} **[Talking:]({self.bot.website})** {str(info['talking']).capitalize()}\n"
            description += f"{bot_emojis['marked_checkbox']} **[GameMode:]({self.bot.website})** {str(info['gamemode']).capitalize()}\n"
            return discord.Embed(description=description, color=self.bot.Blue)

        # Options
        options = []
        for x in guild_data["channels"]:
            options.append(discord.SelectOption(
                label=f"# {guild.get_channel(int(x)).name}", value=x))
        await Dropdown(self.bot, ctx, True, "reply", embed, "Select a channel", 1, 1, options, 10).start()

    @slash_command(name="profile", description=json.load(open("./json/help.json", "r"))["profile"]['desc_short'])
    async def profile(self, ctx: discord.ApplicationContext, target: Optional[Member]):
        # Setup Vars
        fonts = self.bot.fonts
        bot_emojis = self.bot.bot_emojis
        cluster = self.bot.mongodb["Counting"]["User"]
        if target is None:
            target = ctx.author

        # find user data
        user_data = cluster.find_one({"userId": target.id})
        if user_data is None:
            user_data = new_user_data(target.id)

        # if equipped font doesnt exist, set to default
        if str(user_data["equippedFontId"]) not in fonts:
            user_data["equippedFontId"] = 0
            cluster.update_one({"userId": target.id}, {
                "$set": {"equippedFontId": 0}})

        # sort fonts by totalCounted
        user_fonts_Ids = [x for x in user_data["fonts"]]
        user_fonts_Ids.sort(
            key=lambda x: user_data["fonts"][x]["totalCounted"], reverse=True)

        # Embed
        async def embed(page, maxpage, user_fonts_Ids):
            description = f"**Coins:** {bot_emojis['coins']}{user_data['coins']}\n"
            description += f"**Total Counted:** {user_data['totalCounted']}\n"
            description += f"**Monthly Votes:** {user_data['votedCount']}\n"
            if user_data['equippedFontId'] == 0:
                description += f"**Equipped Font:** Default\n"
            else:
                description += f"**Equipped Font:** {fonts[str(user_data['equippedFontId'])]['name']}\n"
            description += f"**Owned Fonts:** {len(user_data['fonts'])}\n"
            # list out owned fonts
            for x in user_fonts_Ids[((page*8) - 8):(page*8)]:
                if x == "0":
                    description += f'**[Default]({self.bot.website})** - [{user_data["fonts"][x]["totalCounted"]}]({self.bot.website})'
                else:
                    description += f'**[{fonts[x]["name"]}]({self.bot.website})** - [{user_data["fonts"][x]["totalCounted"]}]({self.bot.website})'
                description += f'\n{bot_emojis["reply"]}{preview_font(self, x)}\n'

            em = discord.Embed(
                title=f"{target.display_name}'s Profile", description=description, colour=self.bot.Blue)
            em.set_footer(text=f"Page {page}/{maxpage}")
            return em
        await PageButtons(self.bot, ctx, True, "reply", embed, 1, math.ceil(len(user_fonts_Ids)/8), 10, user_fonts_Ids).start()

    @slash_command(name="shop", description=json.load(open("./json/help.json", "r"))["shop"]['desc_short'])
    async def shop(self, ctx: discord.ApplicationContext, page: int = 1):
        fonts = self.bot.fonts
        bot_emojis = self.bot.bot_emojis

        # sort fonts by cost
        font_ids = [x for x in fonts]
        font_ids.sort(key=lambda x: fonts[x]["cost"])

        async def embed(page, maxpage, font_ids):
            description = f""
            for x in font_ids[((page*8) - 8):(page*8)]:
                description += f'**[{fonts[x]["name"]}]({self.bot.website})** - [{bot_emojis["coins"]}{fonts[x]["cost"]}]({self.bot.website})'
                description += f'\n{bot_emojis["reply"]}{preview_font(self, x)}\n'

            em = discord.Embed(
                title=f'', description=f"# Shop\n{description}", colour=self.bot.Blue)
            em.set_footer(text=f"Page {page}/{maxpage}")
            return em
        await PageButtons(self.bot, ctx, True, "reply", embed, page, math.ceil(len(font_ids)/8), 20, font_ids).start()

    @slash_command(name="purchase", description=json.load(open("./json/help.json", "r"))["purchase"]['desc_short'])
    async def purchase(self, ctx: discord.ApplicationContext, font: discord.Option(str, choices=[value["name"] for value in json.load(open("./json/fonts.json", "r")).values()])):
        # Setup Vars
        fonts = self.bot.fonts
        bot_emojis = self.bot.bot_emojis
        cluster = self.bot.mongodb["Counting"]["User"]
        user = ctx.author

        # Get fontId from name
        fontId = None
        for x in fonts:
            if fonts[x]["name"] == font:
                fontId = x
                break
        # Shoudnt happen
        if fontId is None:
            await ctx.respond(embed=discord.Embed(description=f"{bot_emojis['danger']} Not an existing font.", color=self.bot.Red))
            return

        # Find user data
        user_data = cluster.find_one({"userId": user.id})

        # No account
        if user_data is None:
            await ctx.respond(embed=discord.Embed(description=f"{bot_emojis['danger']} Insufficient balance.", color=self.bot.Red))
            return

        # Check if user already has font
        if fontId in user_data["fonts"]:
            await ctx.respond(embed=discord.Embed(description=f"{bot_emojis['danger']} You already have this font.", color=self.bot.Red))
            return

        # Check if user has enough coins
        if user_data["coins"] < fonts[fontId]["cost"]:
            await ctx.respond(embed=discord.Embed(description=f"{bot_emojis['danger']} Insufficient balance.", color=self.bot.Red))
            return

        # calculate new users balance and font
        new_balance = user_data["coins"] - fonts[fontId]["cost"]
        user_data["fonts"][fontId] = {"totalCounted": 0}

        # Update user data
        cluster.update_one({"userId": user.id}, {
            "$set": {"coins": new_balance}})
        cluster.update_one({"userId": user.id}, {
            "$set": {"coins": new_balance, "fonts": user_data["fonts"]}})

        await ctx.respond(embed=discord.Embed(title=f"Purchased {font}", description=f'{preview_font(self, fontId)}', color=self.bot.Green))

    @slash_command(name="equip", description=json.load(open("./json/help.json", "r"))["equip"]['desc_short'])
    async def equip(self, ctx: discord.ApplicationContext, font: discord.Option(str, choices=[value["name"] for value in json.load(open("./json/fonts.json", "r")).values()])):
        # Setup Vars
        fonts = self.bot.fonts
        bot_emojis = self.bot.bot_emojis
        cluster = self.bot.mongodb["Counting"]["User"]
        user = ctx.author

        # Get fontId from name
        fontId = None
        for x in fonts:
            if fonts[x]["name"] == font:
                fontId = x
                break
        # Shoudnt happen
        if fontId is None:
            await ctx.respond(embed=discord.Embed(description=f"{bot_emojis['danger']} Not an existing font.", color=self.bot.Red))
            return

        # Find user data
        user_data = cluster.find_one({"userId": user.id})

        # check if user has font
        if fontId not in user_data["fonts"]:
            await ctx.respond(embed=discord.Embed(description=f"{bot_emojis['danger']} You don't have this font.", color=self.bot.Red))
            return

        # Update user data
        cluster.update_one({"userId": user.id}, {
            "$set": {"equippedFontId": fontId}})

        await ctx.respond(embed=discord.Embed(title=f"Equipped {font}", description=f'{preview_font(self, fontId)}', color=self.bot.Green))

    @slash_command(name="leaderboard", description=json.load(open("./json/help.json", "r"))["leaderboard"]['desc_short'])
    async def leaderboard(self, ctx: discord.ApplicationContext, scope: discord.Option(str, choices=["global", "guild"]), type: discord.Option(str, choices=["counted", "coins"]), page: int = 1):
        # Setup Vars
        cluster = self.bot.mongodb["Counting"]["User"]
        bot_emojis = self.bot.bot_emojis

        # find user data
        user_data = cluster.find()
        user_data = list(user_data)

        # sort by scope
        if scope == "guild":
            user_data = list(filter(lambda x: ctx.guild.get_member(
                x["userId"]) is not None, user_data))

        # sort by type
        if type == "counted":
            user_data.sort(key=lambda x: x["totalCounted"], reverse=True)
        elif type == "coins":
            user_data.sort(key=lambda x: x["coins"], reverse=True)

        # Embed
        async def embed(page, maxpage, user_data):
            description = f""
            for x in user_data[((page*8) - 8):(page*8)]:
                # get user
                user = self.bot.get_user(x["userId"])
                if user is None:
                    user = await self.bot.fetch_user(x["userId"])

                # user discriminator
                discriminator = f'#{user.discriminator}'
                if user.discriminator == "0":
                    discriminator = ""

                # emoji depending on type
                emoji = bot_emojis["coins"]
                if type == "counted":
                    emoji = ""

                description += f'`{user_data.index(x) + 1}.` **{user.name}{discriminator}** - {emoji}{x["totalCounted"]}\n'

            em = discord.Embed(title=f'Leaderboard',
                               description=description, colour=self.bot.Blue)
            em.set_footer(text=f"Page {page}/{maxpage}")
            return em
        await PageButtons(self.bot, ctx, True, "reply", embed, page, math.ceil(len(user_data)/8), 20, user_data).start()

    async def build_web_server(self):
        app = web.Application()

        # mgr = topgg.WebhookManager(client).dbl_webhook(
        #     path="/topgg", auth=self.Secrets["TopGG"])
        # mgr.run(app)

        # @mgr.listener()
        # async def on_topgg_vote(data):
        #     add_vote_rewards(self, int(data["user"]))

        # DiscordBotList – HMAC check
        async def dbl_handler(req: web.Request):
            raw = await req.read()
            sig = req.headers.get("x-dbl-signature", "")
            good = hmac.compare_digest(sig, hmac.new(
                self.Secrets["DBL"], raw, hashlib.sha1).hexdigest())
            if not good:
                return web.Response(status=401)

            payload = json.loads(raw)
            if payload.get("type") == "vote":
                add_vote_rewards(self, int(payload["user"]))
            return web.Response(status=204)

        app.router.add_post("/dbl", dbl_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8080)
        await site.start()
#####################################################################################################################################


def convert_num2emoji(self, number, id):
    """Converts a number to its emoji."""
    number = str(number)
    data = self.bot.fonts
    output = "+" if not number.startswith("-") else ""

    if str(id) == "0":
        return f"{output}{number}"
    if str(id) == "18":
        # pick a random font
        font_ids = list(data.keys())
        id = random.choice(font_ids)
    for x in number:
        output += data[str(id)]["emojiId"][f'{x}']
    return output


def preview_font(self, id):
    """Returns a string of the font from 0-9."""
    if id == "0":  # default
        return "0123456789"
    if id == "18":  # random font
        dice = self.bot.bot_emojis["dice"]
        return f"{dice}{dice}{dice}{dice}{dice}{dice}{dice}{dice}{dice}"

    data = self.bot.fonts
    output = ""
    for x in range(0, 10):
        output += data[id]["emojiId"][f"{x}"]
    return output


def new_guild_data(guild_id):
    """returns a new guild data"""
    guild_data = {"guildId": guild_id,
                  "fonts": {},
                  "channels": {}
                  }
    return guild_data


def new_user_data(user_id):
    """returns a new user data"""
    user_data = {"userId": user_id,
                 "coins": 0,
                 "totalCounted": 0,
                 "votedCount": 0,
                 "fonts": {
                     "0": {
                         "totalCounted": 0,
                     }
                 },
                 "equippedFontId": 0,
                 "equippedGuildsFontId": {}
                 }
    return user_data


def add_vote_rewards(self, uid: int, amt: int = 50):
    cluster_user = self.bot.mongodb["Counting"]["User"]
    user_data = cluster_user.find_one({"userId": uid})
    if user_data is None:
        user_data = new_user_data(uid)
        cluster_user.insert_one(user_data)

    cluster_user.update_one(
        {"userId": uid}, {"$set": {"coins": user_data["coins"] + amt}})
#####################################################################################################################################


def setup(bot):
    bot.add_cog(counting(bot))
