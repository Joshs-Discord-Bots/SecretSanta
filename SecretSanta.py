# https://discord.com/developers/applications
from asyncio.windows_events import NULL
from warnings import WarningMessage
import discord
from discord.ext import commands
import os
from os import system
from discord.ext.commands.core import has_permissions
from discord.gateway import EventListener
import yaml
import random

intents = discord.Intents.default()
# intents.messages = True
# intents.members = True
# intents.guilds = True

activity = discord.Game(name='NAME')
prefix = '**'

bot = commands.Bot(command_prefix = prefix, intents=intents, activity=activity, status=discord.Status.idle, case_insensitive=True)
bot.remove_command('help')

bot.token = 'TOKEN'
with open('token.txt') as f:
    bot.token = f.read()

filename = 'nice_list.yaml'

admins = [285311305253126145, 181862796164726784]

def admin(user):
	return user.id in admins or user.guild_permissions.administrator

def read(readFilename):
	try:
		with open(readFilename) as f:
			return yaml.load(f, Loader=yaml.FullLoader)
	except FileNotFoundError:
		return None

def write(data, writeFilename):
	with open(writeFilename, 'w') as f:
		print('workingdir:', os.getcwd())
		data = yaml.dump(data, f)
	return



system('cls')
print('Booting Up...')



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


# @bot.event
# async def on_error():
# 	print()



@bot.command()
async def join(ctx, user: discord.Member = None):
	if user != None:
		if not admin(ctx.author):
			await ctx.send('You are not allowed to do that!')
			return
	else:
		user = ctx.author
	
	niceList = read(filename)
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
async def remove(ctx, user: discord.Member = None):
	if not admin(ctx.author):
		await ctx.send('You are not allowed to do that!')
		return

	if user == None:
		await ctx.send(f'Usage: `{prefix}remove <user>`')
		return
		
	niceList = read(filename)
	if niceList == None or ctx.guild.id not in niceList or user.id not in niceList[ctx.guild.id]['unshuffled']:
		await ctx.send(f'{user.name} is not on the list!')
	else:
		niceList[ctx.guild.id]['unshuffled'].remove(user.id)
		niceList[ctx.guild.id]['shuffled'].remove(user.id)
		await ctx.send(f'{user.name} has been taken off the list!')
	write(niceList, filename)



@bot.command()
async def list(ctx):
	niceList = read(filename)
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

	niceList = read(filename)
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

	niceList = read(filename)
	if niceList == None or ctx.guild.id not in niceList or len(niceList[ctx.guild.id]['unshuffled']) == 0:
		await ctx.send('Cant view/shuffle an empty list!')
		return

	shuffledList = niceList[ctx.guild.id]['shuffled']

	if view == '':
		random.shuffle(shuffledList)
		niceList[ctx.guild.id]['shuffled'] = shuffledList
		write(niceList, filename)
		await ctx.send(f'List has been shuffled!\nView it with `{prefix}shuffle view`')
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
		await ctx.send(f'Usage: `{prefix}shuffle [view]`')



@bot.command()
async def start(ctx):
	if not admin(ctx.author): # Check if user is admin
		await ctx.send('You are not allowed to do that!')
		return

	niceList = read(filename) # Check if enough people on list
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
		curr = await bot.fetch_user(shuffledList[i])
		pair = await bot.fetch_user(shuffledList[(i+1) % len(shuffledList)])
		# await ctx.send(f'{curr.name} -> {pair.name}')
		await curr.send(f'Ho Ho Ho!\nYour secret santa recipient is {pair.name}!')



@bot.command()
async def help(ctx):
	embed = discord.Embed ( # Message
		title='Help',
		colour=discord.Colour.green(),
	)
	embed.add_field(name='join', value='Add yourself to the list', inline=False)
	embed.add_field(name='join <user>', value='Add a specified user to the list\n(admin only)', inline=False)
	embed.add_field(name='remove <user>', value='Removes a user to the list\n(admin only)', inline=False)
	embed.add_field(name='list', value='Lists everyone currently on the list', inline=False)
	embed.add_field(name='clear', value='Clears the current secret santa list\n(admin only)', inline=False)
	embed.add_field(name='shuffle', value='Shuffles the list and assigns each member with a random recipient\n(admin only)', inline=False)
	embed.add_field(name='shuffle view', value='DMs you the current secret santa pairings\n(admin only)', inline=False)
	embed.add_field(name='start', value='Starts the secret santa, DMing each member with their assigned recipient\n(admin only)', inline=False)
	await ctx.send(embed=embed)



bot.run(bot.token)