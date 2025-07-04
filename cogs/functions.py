import json
import discord

async def get_webhook(self, ctx):
    """Returns a webhook in the current channel. If none is found, it creates a new one.
    
    :code:`get_webhook(self, ctx)`
    
    Attributes
    ----------
    ctx : discord.ext.commands.Context
        The context of the command.
    """
    # Find webhook
    webhook = False
    for w in await ctx.channel.webhooks():
        if w.user == self.bot.user:
            webhook = w
            break
    # Not found, create webhook
    if webhook == False:
        webhook = await ctx.channel.create_webhook(name=self.bot.user, avatar=None, reason=None)
    return webhook

def emojibar(emojis, value, maxValue, size):
    """Returns a string of emojis that represents a bar graph.
    
    :code:`emojibar(emojis, value, maxValue, size)`

    Attributes
    ----------
    emojis : dict
        A dictionary of emojis that will be used to create the bar graph.\n
        The dictionary must contain the following keys:\n
        (bar1_empty, bar1_half, bar1_full, bar1_full2, bar2_empty, bar2_half, bar2_full, bar2_full2, bar3_empty, bar3_half, bar3_full)
    value : float
        The value of the bar graph.
    maxValue : float
        The maximum value of the bar graph.
    size : int
        The number of emojis that will be used to create the bar graph.
    """
    bar_array = []
    percentage = round((value / maxValue) * size, 1)
    for i in range(size):
        # first bar
        if i == 0:
            # if percentage less than 0.3, then add empty bar
            if percentage < 0.3:
                bar_array.append(emojis["bar1_empty"])
            # if percentage less than or equal to 0.7, then add half bar
            elif percentage <= 0.7:
                bar_array.append(emojis["bar1_half"])
            # if percentage is less than or equal to 1.3, then add full bar that cutoff
            elif percentage <= 1.3:
                bar_array.append(emojis["bar1_full2"])
            # if percentage is greater than 1.3, then add full bar
            elif percentage > 1.3:
                bar_array.append(emojis["bar1_full"])
        # middle bars
        elif 0 < i < (size - 1):
            # if percentage is less than 0.3, then add empty bar
            if (percentage - i) < 0.3:
                bar_array.append(emojis["bar2_empty"])
            # if percentage is less than or equal to 0.7, then add half bar
            elif (percentage - i) <= 0.7:
                bar_array.append(emojis["bar2_half"])
            # if percentage is less than or equal to 1.3, then add full bar that cutoff
            elif (percentage - i) <= 1.3:
                bar_array.append(emojis["bar2_full2"])
            # if percentage is greater than 1.3, then add full bar
            elif (percentage - i) > 1.3:
                bar_array.append(emojis["bar2_full"])
        # last bar
        else:
            # if percentage is less than 0.3, then add empty bar
            if (percentage - i) < 0.3:
                bar_array.append(emojis["bar3_empty"])
            # if percentage is less than or equal to 0.7, then add half bar
            elif (percentage - i) <= 0.7:
                bar_array.append(emojis["bar3_half"])
            else:
                bar_array.append(emojis["bar3_full"])
    return "".join(bar_array)

def user_avatar_url(user):
    try: 
        user_avatar_url = user.avatar.url
    except: 
        user_avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"
    return user_avatar_url

async def response(slash, type, ctx, *args, **kwargs):
    """ Hybrid response function for slash and normal commands

    :code:`response(slash, type, ctx, *args, **kwargs)`

    Attributes
    ----------
    slash: bool
        True if slash command, False if normal command
    type: str
        "send", "reply", "edit"
    ctx: discord.ext.commands.Context or discord_slash.context.SlashContext
        Context of the command
    *args: list
        Positional arguments for the response function
    **kwargs: dict
        Keyword arguments for the response function
    """
    if type == "send":
        return await ctx.send(*args, **kwargs)

    if slash == True:
        #remove uncompatible **kwargs
        if "mention_author" in kwargs:
            kwargs.pop("mention_author")

        if type == "reply":
            return await ctx.respond(*args, **kwargs)
        if type == "edit":
            #return await ctx.edit_original_response(*args, **kwargs)
            return await ctx.edit(*args, **kwargs)
    
    if slash == False:
        #remove uncompatible **kwargs
        if "ephemeral" in kwargs:
            kwargs.pop("ephemeral")
        if type == "reply":
            return await ctx.reply(*args, **kwargs)
        if type == "edit":
            return await ctx.edit(*args, **kwargs)

class PageButtons(discord.ui.View):
    """Create a basic page button menu.

    :code:`PageButtons(bot, ctx, slash, function, page, maxpage, timeout, *args, **kwargs)`

    Attributes
    ----------
    bot: :class:`discord.ext.commands.Bot`
        The bot object.
    ctx: :class:`discord.ext.commands.Context`
        The context object.
    slash: :class:`bool`
        If the command is a slash command.
    type: :class:`str`
        The type of response. Can be "send" or "reply"
    function: :class:`function`
        The function must follow this format:
            1: :code:`async def function(page, maxpage, *args, **kwargs)`
            2: :code:`"your code here"`
            3: :code:`return embed`
    page: :class:`int`
        The current page.
    maxpage: :class:`int`
        The max page.
    timeout: :class:`int`
        The timeout for the menu.
    *args: :class:`tuple`
        The arguments to be passed to the function.
    **kwargs: :class:`dict`
        The keyword arguments to be passed to the function.
    """
    def __init__(self, bot, ctx, slash, type, function, page, maxpage, timeout, *args, **kwargs):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.ctx = ctx
        self.slash = slash
        self.type = type
        self.function = function
        self.page = page
        self.maxpage = maxpage
        self.args = args
        self.kwargs = kwargs
    
    @discord.ui.button(style=discord.ButtonStyle.primary)
    async def first(self, button: discord.ui.Button, interaction: discord.Interaction):
        # quick response (prevent timeout)
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        
        # actual response
        self.page = 1
        embed = await self.function(self.page, self.maxpage, *self.args, **self.kwargs)
        
        self.enable_all_items()
        self.children[0].disabled = True
        self.children[1].disabled = True
        self.children[2].disabled = False
        self.children[3].disabled = False
        
        await response(self.slash, "edit", self.message, embed=embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary)
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        # quick response (prevent timeout)
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        
        # actual response
        if self.page > 1:
            self.page -= 1
        embed = await self.function(self.page, self.maxpage, *self.args, **self.kwargs)
        
        self.enable_all_items()
        self.children[2].disabled = False
        self.children[3].disabled = False
        if self.page == 1:
            self.children[0].disabled = True
            self.children[1].disabled = True
            
        await response(self.slash, "edit", self.message, embed=embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        # quick response (prevent timeout)
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        
        # actual response
        if self.page < self.maxpage:
            self.page += 1
        embed = await self.function(self.page, self.maxpage, *self.args, **self.kwargs)
        
        self.enable_all_items()
        self.children[0].disabled = False
        self.children[1].disabled = False
        if self.page == self.maxpage:
            self.children[2].disabled = True
            self.children[3].disabled = True
        
        await response(self.slash, "edit", self.message, embed=embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary)
    async def last(self, button: discord.ui.Button, interaction: discord.Interaction):
        # quick response (prevent timeout)
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        
        # actual response
        self.page = self.maxpage
        embed = await self.function(self.page, self.maxpage, *self.args, **self.kwargs)
        
        self.enable_all_items()
        self.children[0].disabled = False
        self.children[1].disabled = False
        self.children[2].disabled = True
        self.children[3].disabled = True
        
        await response(self.slash, "edit", self.message, embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.ctx.author.id:
            return True
        await interaction.response.send_message(embed=discord.Embed(description="You are not the author of the command.", color=self.bot.Red), ephemeral=True)
        return False

    async def on_timeout(self):
        self.disable_all_items()
        await response(self.slash, "edit", self.message, view=self)
        
    async def start(self):
        self.children[0].emoji = self.bot.bot_emojis['double_arrow_left']
        self.children[1].emoji = self.bot.bot_emojis['arrow_left']
        self.children[2].emoji = self.bot.bot_emojis['arrow_right']
        self.children[3].emoji = self.bot.bot_emojis['double_arrow_right']
        
        # quick response (prevent timeout)
        self.disable_all_items()
        embed = discord.Embed(description=f"{self.bot.bot_emojis['spinning_cog']}", colour=self.bot.Blue)
        self.message = await response(self.slash, self.type, self.ctx, embed=embed, view=self)
        
        # actual response
        self.enable_all_items()
        embed = await self.function(self.page, self.maxpage, *self.args, **self.kwargs)
        await response(self.slash, "edit", self.message, embed=embed, view=self)
        
class Dropdown(discord.ui.View):
    def __init__(self, bot, ctx, slash, type, function, placeholder, min_values, max_values, options, timeout, *args, **kwargs):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.ctx = ctx
        self.slash = slash
        self.type = type
        self.function = function
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.options = options
        self.args = args
        self.kwargs = kwargs
    
    @discord.ui.select(
        placeholder = "Select an option",
        min_values = 1, 
        max_values = 1, 
        options = [
            discord.SelectOption(
                label="Vanilla",
                description="Pick this if you like vanilla!"
            ),
            discord.SelectOption(
                label="Chocolate",
                description="Pick this if you like chocolate!"
            ),
            discord.SelectOption(
                label="Strawberry",
                description="Pick this if you like strawberry!"
            )
        ]
    )
    async def dropdown(self, select, interaction):
        embed = await self.function(select.values, *self.args, **self.kwargs)
        await interaction.response.edit_message(embed=embed, view=self)
        
    async def on_timeout(self):
        for button in self.children:
            button.disabled = True
        await response(self.slash, "edit", self.message, view=self)
        
    async def start(self):
        self.dropdown.placeholder = self.placeholder
        self.dropdown.min_values = self.min_values
        self.dropdown.max_values = self.max_values
        self.dropdown.options = self.options
        
        embed = await self.function(0, *self.args, **self.kwargs)
        self.message = await response(self.slash, self.type, self.ctx, embed=embed, view=self)