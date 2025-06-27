import dbl
import discord
from discord.ext import commands

class TopGG(commands.Cog):
	""" Handles interactions with the top.gg API. """

	def __init__(self, bot) -> None:
		""" Class init method. """

		self.bot = bot
		self.token = self.Secrets[]
		# Autopost will post your guild count every 30 minutes
		self.dblpy = dbl.DBLbot(self.bot, self.token, autopost=True, webhook_path='/dblwebhook', webhook_auth=os.getenv('DBL_WEBHOOK_PASSWORD'), webhook_port=5000) 
	
	@commands.Cog.listener()
	async def on_dbl_vote(self, data) -> None:
		""" Message user when they vote. and give rewards. """

	@commands.Cog.listener()
	async def on_dbl_test(self, data) -> None:
		""" Tests the webhook. """
		print('Test vote!')
		
#####################################################################################################################################

def setup(bot):
    bot.add_cog(TopGG(bot))