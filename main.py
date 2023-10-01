from typing import Optional

import discord
from discord import app_commands

import ilevia
import ed

# Logging
import logger
from logger import *
logger.MAINPREFIX = "[DiscordBot]"

logger.INFO  = True
logger.DEBUG = False
logger.WARN  = True
logger.ERROR = True


SERVER = discord.Object(id=932927456594231357)  # replace with your guild id

class MyClient(discord.Client):
	def __init__(self, *, intents: discord.Intents):
		super().__init__(intents=intents)
		# A CommandTree is a special type that holds all the application command
		# state required to make it work. This is a separate class because it
		# allows all the extra state to be opt-in.
		# Whenever you want to work with application commands, your tree is used
		# to store and work with them.
		# Note: When using commands.Bot instead of discord.Client, the bot will
		# maintain its own tree instead.
		self.tree = app_commands.CommandTree(self)

	# In this basic example, we just synchronize the app commands to one guild.
	# Instead of specifying a guild to every command, we copy over our global commands instead.
	# By doing so, we don't have to wait up to an hour until they are shown to the end-user.
	async def setup_hook(self):
		# This copies the global commands over to your guild.
		self.tree.copy_global_to(guild=SERVER)
		await self.tree.sync(guild=SERVER)


intents = discord.Intents.default()
client = MyClient(intents=intents)

# Channels
ILEVIA, ED = 2 * [None]

ILEVIAID = 1104791483866947605
EDID = 1123688395273683054

# Data
ileData = None


@client.event
async def on_ready():
	global ILEVIA, _
	info(f'Logged in as {client.user} (ID: {client.user.id})')
	info('------')

	# Set channels id
	ILEVIA = client.get_channel(ILEVIAID)
	ED = client.get_channel(EDID)


@client.tree.command(name="search", description="Search for lines, stop in ilevia network")
@app_commands.guilds(SERVER)
@app_commands.rename(resultNum = "result_number")
@app_commands.describe(
	query = "The query to submit to ilevia",
	resultNum = "The number of result which will be displayed (defaut : 5)"
)
async def search(interaction: discord.Interaction, query: str, resultNum: int = 5):
	await interaction.response.defer()
	result = ilevia.search(query, resultNum)
	if type(result) == int:
		if result == 1: # If no result, return
			await interaction.followup.send(f"No result found for the query : {query}.\nExit code : {result}")
			return
		else:
			await interaction.followup.send(f"An error occurred during the execution of the function {ilevia.search.__name__} from module {ilevia.__name__}.\nExit code : {result}")
			return

	global ileData
	ileData = result

	message = ""
	if "lines" in result: message += "Found lines :\n\t" + ", ".join(sorted(list(result["lines"]))) # Indenting text
	if "stops" in result: message += "\n\nFound stops :\n\t" + "\n\t".join(result["stops"])

	await interaction.followup.send(message)

async def outputSchedules(schedules: dict | int, interaction: discord.Interaction, extraMsg: str = "not given") -> None:
	if type(schedules) == int:
		match schedules:
			case 1:
				await interaction.followup.send(f"No result found with the query : {extraMsg}. Check your previous search.\nExit code : {schedules}")
				return
			case 2:
				await interaction.followup.send(f"There is no line passing at the selected stop.\nExit code : {schedules}")
				return
			case 3:
				await interaction.followup.send(f"Index out of range with position : {extraMsg}.\nExit code : {schedules}")
				return
			case _:
				await interaction.followup.send(f"An error occurred during the execution of the function {ilevia.selectpos.__name__} from module {ilevia.__name__}.\nExit code : {schedules}")
				return

	message = ""
	for line in schedules:
		if len(schedules[line]) == 0: continue
		message += f"{line} :\n"
		for direction in schedules[line]:
			if len(schedules[line][direction]) == 0: continue
			message += f"\t{direction} : \n"
			message += "\t\t" + "\n\t\t".join(schedules[line][direction]) + "\n"

	while len(message) > 2000:
		splitPos = len(message) - message[::-1].find("\n", len(message) - 2000)
		await interaction.followup.send(message[:splitPos])
		message = message[splitPos:]

	await interaction.followup.send(message)


@client.tree.command(name="select", description="Select a stop or a line to see there schedules")
@app_commands.guilds(SERVER)
@app_commands.rename(resultNum = "result_number")
@app_commands.describe(
	query = "The query to find in previous search",
	resultNum = "The number of max lines which can be displayed (defaut : 52)"
)
async def select(interaction: discord.Interaction, query: str, resultNum: int = 52):
	if ileData == None or len(ileData) == 0:
		await interaction.response.send_message(f"You didn't made any search before. Use /search")
		return

	await interaction.response.defer()
	await outputSchedules(ilevia.select(query, ileData, resultNum), interaction, query)
	
@client.tree.command(name="selectpos", description="Select a stop or a line by position")
@app_commands.guilds(SERVER)
@app_commands.rename(resultNum = "result_number")
@app_commands.describe(
	pos = "The position of the stop in your previous search (starting from 1)",
	resultNum = "The number of max lines which can be displayed (defaut : 52)"
)
async def selectpos(interaction: discord.Interaction, pos: int, resultNum: int = 52):
	if ileData == None or len(ileData) == 0:
		await interaction.response.send_message(f"You didn't made any search before. Use /search")
		return

	await interaction.response.defer()
	await outputSchedules(ilevia.selectpos(pos, ileData, resultNum), interaction, pos)

###################################################################################################
###################################################################################################
###################################################################################################
# EcoleDirecte

edData = {}

@client.tree.command(name="login", description="Log in EcoleDirecte")
@app_commands.guilds(SERVER)
@app_commands.rename(id_ = "username", mdp = "password", saveIds = "save_your_ids")
@app_commands.describe(
	id_ = "Your EcoleDirecte username",
	mdp = "Your EcoleDirecte password",
	saveIds = "If true, your ids will be saved, and you wont have to retype your password"
)
async def login(interaction: discord.Interaction, id_: str, mdp: str = None, saveIds: bool = True):
	if mdp == None: mdp = ""
	ids = ed.Login(id_, mdp, str(interaction.user.id), storeIds = saveIds)

	password = ids.getIds()
	if password == 1:
		await interaction.response.send_message("You havn't gave any password and you are not registered in our database")
		return

	edOject = ed.EcoleDirecte(ids)
	edData[interaction.user.id] = edOject

	exception = edOject.login()
	if type(exception) == str:
		await interaction.response.send_message(f"The login failed with username : \"{edOject.username}\", with error : \"{exception}\"")
		return
	elif exception == 2:
		await interaction.response.send_message(f"The username \"{ids.id}\" is not registered in our database")
		return
	elif exception == 3:
		await interaction.response.send_message(f"Your discord account is not link to the account \"{ids.id}\"")
		return

	#await interaction. # TODO delete login message for security
	await interaction.response.send_message(f"Successfully logged in with username \"{edOject.username}\"")

@client.tree.command(name="deluser", description="Delete your id & password from our database")
@app_commands.guilds(SERVER)
@app_commands.rename(id_ = "username", mdp = "password")
@app_commands.describe(
	id_ = "Your EcoleDirecte username",
	mdp = "Your EcoleDirecte password to check if thats you :)",
)
async def delUser(interaction: discord.Interaction, id_: str, mdp: str):
	if mdp == "":
		await interaction.response.send_message("You havn't gave any password. Enter your password so we can verify its you")
		return

	try:
		edObject = edData[interaction.user.id]
	except KeyError:
		await interaction.response.send_message("Your account is not link to an EcoleDirecte account, try using /login or /link to link it again")
		return

	ids = edObject.reloadIds()
	if id_ == ids[0] and mdp == ids[1]:
		edData[interaction.user.id].ids.clearIds()
		del edData[interaction.user.id]
		await interaction.response.send_message("Successfully remove your account from our database")
	elif mdp == ids[1]:
		await interaction.response.send_message("Wrong username")
	elif id_ == ids[0]:
		await interaction.response.send_message("Wrong password")
	else:
		await interaction.response.send_message("Wrong username & password")

@client.tree.command(name="planning", description="Get your planning for 2 weeks")
@app_commands.guilds(SERVER)
async def planning(interaction: discord.Interaction):
	userId = interaction.user.id

	if userId not in edData:
		await interaction.response.send_message("Login before pls ^^")
		return

	await interaction.response.defer()

	edObject = edData[userId]
	filepath = edObject.planning2image(str(userId))

	await interaction.followup.send(file=discord.File(str(filepath)))


if __name__ == '__main__':
	logger.MAINPREFIX = ""

client.run('')

# ._.																															._.		...
