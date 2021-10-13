import discord
from discord.ext import commands
import os
from os import system
import random
import json

#region Init

def read(readFilename):
	try:
		with open(readFilename) as json_file:
			return json.load(json_file)
	except FileNotFoundError:
		return None

def write(data, writeFilename):
	with open(writeFilename, 'w') as outfile:
		json.dump(data, outfile, indent=4)
	return

def convertDictionaryKeyFromStringToInteger(oldDict):
	newDict = {}
	for oldKey in oldDict:
		if isinstance(oldKey, str):
			newKey = int(oldKey)
			newDict[newKey] = oldDict[oldKey]
		else:
			newDict[oldKey] = oldDict[oldKey]
	return newDict


if not os.path.isfile('config.json'):
	def_config = {
		'token': 'TOKEN',
		'name': 'BOT NAME',
		'intents': {'messages': False, 'members': False, 'guilds': False},
		'prefix': '-',
		'admins': []
	}
	write(def_config, 'config.json')

config = read('config.json')

intents = discord.Intents.default()
intents.messages = config['intents']['messages']
intents.members = config['intents']['members']
intents.guilds = config['intents']['guilds']


activity = discord.Game(name=f"{config['prefix']}help")
bot = commands.Bot(command_prefix = config['prefix'], intents=intents, activity=activity, status=discord.Status.online, case_insensitive=True)
bot.remove_command('help')

bot.token = config['token']
bot.admins = config['admins']

filename = 'data/nice_list.json'

def admin(user):
	return user.id in bot.admins or user.guild_permissions.administrator


system('cls')
print('Booting Up...')

#endregion

@bot.event
async def on_ready():
	system('cls')
	print(f'{bot.user} has connected to Discord!')


@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.MemberNotFound):
		await ctx.send('That user does not exist!')
	elif isinstance(error, commands.MissingPermissions):
		await ctx.send('You are not allowed to do that!')

@bot.command()
async def join(ctx, user: discord.Member = None):
	if user != None:
		if not admin(ctx.author):
			await ctx.send('You are not allowed to do that!')
			return
	else:
		user = ctx.author
	
	niceList = convertDictionaryKeyFromStringToInteger(read(filename))
	if niceList == None:
		niceList = {}
	if ctx.guild.id not in niceList or niceList[ctx.guild.id]['unshuffled'] == []:
		niceList[ctx.guild.id] = {'unshuffled' : [], 'shuffled' : []}
	if user.id not in niceList[ctx.guild.id]['unshuffled']:
		niceList[ctx.guild.id]['unshuffled'].append(user.id)
		niceList[ctx.guild.id]['shuffled'].append(user.id)
		await ctx.send(f'{user.name} has been put on the nice list!')
	else:
		await ctx.send(f'{user.name} is already on the nice list!')
	write(niceList, filename)

@bot.command()
async def setPrefix(ctx, char = None):
	if not admin(ctx.author):
		await ctx.send('You are not allowed to do that!')
	elif char == None:
		await ctx.send(f'Usage: `{bot.command_prefix}setPrefix <char>`')
		return
	else:
		config['prefix'] = char[0]
		write(config, 'config.json')
		bot.command_prefix = char[0]
		await bot.change_presence(activity=discord.Game(name=f"{bot.command_prefix}help"))
		await ctx.send(f'Bot command prefix changed to `{bot.command_prefix}`')

@bot.command()
async def remove(ctx, user: discord.Member = None):
	if not admin(ctx.author):
		await ctx.send('You are not allowed to do that!')
		return

	if user == None:
		await ctx.send(f'Usage: `{bot.command_prefix}remove <user>`')
		return
		
	niceList = convertDictionaryKeyFromStringToInteger(read(filename))
	if niceList == None or ctx.guild.id not in niceList or user.id not in niceList[ctx.guild.id]['unshuffled']:
		await ctx.send(f'{user.name} is not on the list!')
	else:
		niceList[ctx.guild.id]['unshuffled'].remove(user.id)
		niceList[ctx.guild.id]['shuffled'].remove(user.id)
		await ctx.send(f'{user.name} has been taken off the list!')
	write(niceList, filename)


@bot.command()
async def leave(ctx):
	user = ctx.author
	niceList = convertDictionaryKeyFromStringToInteger(read(filename))
	if niceList == None or ctx.guild.id not in niceList or user.id not in niceList[ctx.guild.id]['unshuffled']:
		await ctx.send('You are not on the list!')
	else:
		niceList[ctx.guild.id]['unshuffled'].remove(user.id)
		niceList[ctx.guild.id]['shuffled'].remove(user.id)
		await ctx.send('You have been taken off the list!')
	write(niceList, filename)


@bot.command()
async def list(ctx):
	niceList = convertDictionaryKeyFromStringToInteger(read(filename))
	embed = discord.Embed ( # Message
		title='Secret Santa List',
		colour=discord.Colour.green()
	)
	if niceList == None or ctx.guild.id not in niceList or niceList[ctx.guild.id]['unshuffled'] == None:
		embed.description = 'There is no one on the list!'
	else:
		list = ''
		for userid in niceList[ctx.guild.id]['unshuffled']:
			user = await bot.fetch_user(userid)
			list+=f'\n{user.name}'
		embed.description = list
	await ctx.send(embed=embed)

@bot.command()
async def clear(ctx):
	if not admin(ctx.author):
		await ctx.send('You are not allowed to do that!')
		return

	niceList = convertDictionaryKeyFromStringToInteger(read(filename))
	if niceList == None or ctx.guild.id not in niceList or len(niceList[ctx.guild.id]['unshuffled']) == 0:
		await ctx.send('List is already empty!')
		return
	


	await ctx.send('You are about to clear the current list!\nTo continue, please type "confirm clear"')

	def check(m): # Check if author sent responce in same channel
		return m.author == ctx.author and m.channel == ctx.channel

	msg = await bot.wait_for('message', check=check)
	if msg.content != 'confirm clear': # if confirmed
		await ctx.send('The list was NOT cleared!')
		return

	niceList[ctx.guild.id]['unshuffled'] = []
	niceList[ctx.guild.id]['shuffled'] = []
	write(niceList, filename)
	await ctx.send('The list has now been cleared!')

@bot.command()
async def shuffle(ctx, view = ''):
	if not admin(ctx.author):
		await ctx.send('You are not allowed to do that!')
		return

	niceList = convertDictionaryKeyFromStringToInteger(read(filename))
	if niceList == None or ctx.guild.id not in niceList or len(niceList[ctx.guild.id]['unshuffled']) == 0:
		await ctx.send('Cant view/shuffle an empty list!')
		return

	shuffledList = niceList[ctx.guild.id]['shuffled']

	if view == '':
		random.shuffle(shuffledList)
		niceList[ctx.guild.id]['shuffled'] = shuffledList
		write(niceList, filename)
		await ctx.send(f'List has been shuffled!\nView it with `{bot.command_prefix}shuffle view`')
	elif view.lower() == 'view':
		await ctx.send('DMing shuffled list...')
		embed = discord.Embed (
		title='Shuffled Secret Santa List',
		colour=discord.Colour.green()
		)
		for i, userid in enumerate(shuffledList):
			curr = await bot.fetch_user(shuffledList[i])
			pair = await bot.fetch_user(shuffledList[(i+1) % len(shuffledList)])
			embed.add_field(name=curr.name, value=pair.name, inline=False)
		await ctx.author.send(embed=embed)
	else:
		await ctx.send(f'Usage: `{bot.command_prefix}shuffle [view]`')

@bot.command()
async def start(ctx):
	if not admin(ctx.author): # Check if user is admin
		await ctx.send('You are not allowed to do that!')
		return

	niceList = convertDictionaryKeyFromStringToInteger(read(filename)) # Check if enough people on list
	if niceList == None or ctx.guild.id not in niceList or len(niceList[ctx.guild.id]['unshuffled']) < 3:
		await ctx.send('You need at least 3 people on the list!')
		return

	await ctx.send('You are about to start the secret santa!\nTo continue, please type "confirm start"')

	def check(m): # Check if author sent responce in same channel
		return m.author == ctx.author and m.channel == ctx.channel

	msg = await bot.wait_for('message', check=check)
	if msg.content != 'confirm start': # if confirmed
		await ctx.send('The secret santa has been canceled!')
		return

	await ctx.send('Sending out your secret santa recipients now!')

	shuffledList = niceList[ctx.guild.id]['shuffled']
	for i, userid in enumerate(shuffledList):
		curr = ctx.guild.get_member(shuffledList[i])
		pair = ctx.guild.get_member(shuffledList[(i+1) % len(shuffledList)])
		# await ctx.send(f'{curr.name} -> {pair.name}')
		if pair.nick == None:
			await curr.send(f'Ho Ho Ho!\nYour secret santa recipient is {pair.name}!')
		else:
			await curr.send(f'Ho Ho Ho!\nYour secret santa recipient is {pair.nick}! ({pair.name})')
	await ctx.send('Messages sent! Ho ho ho')
	

@bot.command()
async def admins(ctx, action='list', user: discord.Member = None):
	if action == 'list':
		embed = discord.Embed (
			title='Secret Santa Admins',
			colour=discord.Colour.green()
		)
		list = ''
		for userid in config['admins']:
			user = await bot.fetch_user(userid)
			list+=f'\n{user.name}'
		embed.description = list
		await ctx.send(embed=embed)
		return
	elif not admin(ctx.author):
		await ctx.send('You do not have permission to do that!')
		return
	
	if user == None:
		user == ctx.author
	
	if action == 'add':
		if user.id in config['admins']:
			await ctx.send(f'"{user.name}" is already an admin!')
		else:
			config['admins'].append(user.id)
			write(config, 'config.json')
			await ctx.send(f'"{user.name}" is now an admin')
	elif action == 'remove':
		if user.id not in config['admins']:
			await ctx.send(f'"{user.name}" is not an admin!')
		else:
			config['admins'].remove(user.id)
			write(config, 'config.json')
			await ctx.send(f'"{user.name}" is no longer an admin')
	else:
		await ctx.send(f'Usage: `{bot.command_prefix} admin add/remove <user>`')



@bot.command()
async def ping(ctx):
	await ctx.send('Pong!')

@bot.command()
async def reload(ctx):
	if admin(ctx.author):
		await ctx.send('Reloading...')
		os.system('run.bat')
		quit()
	else:
		await ctx.send('You do not have permission to do that!')

@bot.command()
async def help(ctx):
	embed = discord.Embed ( # Message
		title='Help',
		colour=discord.Colour.green(),
	)
	embed.add_field(name='join', value='Add yourself to the list', inline=False)
	embed.add_field(name='join <user>', value='Add a specified user to the list\n(admin only)', inline=False)
	embed.add_field(name='leave', value='Remove yourself from the list', inline=False)
	embed.add_field(name='remove <user>', value='Removes a user to the list\n(admin only)', inline=False)
	embed.add_field(name='list', value='Lists everyone currently on the list', inline=False)
	embed.add_field(name='clear', value='Clears the current secret santa list\n(admin only)', inline=False)
	embed.add_field(name='shuffle', value='Shuffles the list and assigns each member with a random recipient\n(admin only)', inline=False)
	embed.add_field(name='shuffle view', value='DMs you the current secret santa pairings\n(admin only)', inline=False)
	embed.add_field(name='start', value='Starts the secret santa, DMing each member with their assigned recipient\n(admin only)', inline=False)
	
	embed.add_field(name='admins list', value='Lists users who have access to admin commands', inline=False)
	embed.add_field(name='admins add <user>', value='Give user access to admin commands\n(admin only)', inline=False)
	embed.add_field(name='admins remove <user>', value='Revoke user\'s access to admin commands\n(admin only)', inline=False)
	
	embed.add_field(name='setPrefix <char>', value='Change bot\'s prefix\n(admin only)', inline=False)
	await ctx.send(embed=embed)



bot.run(bot.token)