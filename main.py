# Works with Python 3.6
import asyncio
import json
import os
import time
import discord
import requests
from discord.ext import commands
from discord.ext.commands import Bot
from mcstatus import MinecraftServer

try:
	fileName = "all_status.json"
	with open(fileName, "r") as f:
		all_status = json.load(f)
except:
	with open(fileName, "w") as f:
		json.dump({}, f)
		all_status = {}

client = commands.Bot(command_prefix = "##")

client.remove_command('help')

shupik = "C:\\Users\\Shupik desu\\Desktop\\Programing\\Bot\\McStatus_token.json"
with open(shupik, "r") as f:
		token = json.load(f)[0]

def t_ip(ip, port):
	return "{0}:{1}".format(ip,port)

def save(guild, category, channel, ip, port):
	data = {
		"category":category.id,
		"channel":channel.id,
	}

	try:
		all_status[guild.id][t_ip(ip,port)] = data
	except:
		all_status[guild.id] = {t_ip(ip,port) : data}

	with open(fileName, "w") as f:
		json.dump(all_status, f, indent=4)

def d_remove(guild, ip, port):
	del all_status[guild.id][t_ip(ip,port)]

	with open(fileName, "w") as f:
		json.dump(all_status, f, indent=4)



@client.event
async def on_ready():
	# just saying that the bot is on
	print('Logged in as')
	print(client.user.name)
	print(client.user.id)
	print('------')
	global starttime
	starttime = time.time()

	servers = []
	for guild in all_status:
		for ip in all_status[guild]:
			servers.append(ip)
	servers = list(set(servers))

	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="{} Minecraft Servers".format(len(servers))))



async def mcstatusloop():
	global all_status
	await client.wait_until_ready()

	while True:
		
		servers = []
		for guild in all_status:
			for ip in all_status[guild]:
				servers.append(ip)
		servers = list(set(servers))

		await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="{} Minecraft Servers".format(len(servers))))


		for guild in all_status:
			for full_ip in all_status[guild]:
				
				try:
					server = MinecraftServer.lookup("{0}".format(full_ip))
					status = server.status()
					channel_name = "Server Online ({0}/{1})".format(status.players.online,status.players.max)

					channel = client.get_channel(all_status[guild][full_ip]["channel"])
					await channel.edit(name=channel_name)

				except:
					channel = client.get_channel(all_status[guild][full_ip]["channel"])
					await channel.edit(name="Server Offline")

		await asyncio.sleep(30)


@client.command(pass_context = True)
async def help(ctx):
	embed=discord.Embed(title=" ", color=0x5edbff)
	embed.set_author(name="McStatus Help")
	embed.add_field(name="##help", value="I think you would know", inline=False)
	embed.add_field(name="##setup [ip] \{port\}", value="Sets up an McStatus for that server", inline=False)
	embed.add_field(name="##remove [ip] \{port\}", value="Removes the McStatus for that server", inline=False)
	embed.add_field(name="##botstatus", value="Tells you how long it has been running", inline=False)
	embed.add_field(name="##ping [ip] \{port\}", value="Gets the status of a Minecraft server", inline=False)
	await ctx.send(embed=embed)



@client.command(pass_context = True)
async def botstatus(ctx):
	# gets the current up time of the bot
	global starttime
	current_time = round(time.time() - starttime)
	second = current_time % 60
	minute = (current_time // 60) % 60
	hour = current_time // 3600
	
	await ctx.send("{name} has been running for {hour} hr, {minute} min, {second} sec.".format(name=client.user.name, hour=hour, minute=minute, second=second))



@client.command(pass_context = True)
async def ping(ctx, ip, port=25565):
	try:
		server = MinecraftServer.lookup("{0}:{1}".format(ip,port))
		status = server.status()
		if status.players.online == status.players.max:
			embed=discord.Embed(color=0xfffb00)
			embed.add_field(name=t_ip(ip,port), value="Server Full ({0}/{1})".format(status.players.online,status.players.max), inline=False)
			await ctx.send(embed=embed)
		else:
			embed=discord.Embed(color=0x17ff28)
			embed.add_field(name=t_ip(ip,port), value="Server Online ({0}/{1})".format(status.players.online,status.players.max), inline=False)
			await ctx.send(embed=embed)
	except:
		embed=discord.Embed(color=0xff1717)
		embed.add_field(name=t_ip(ip,port), value="Server Offline", inline=False)
		await ctx.send(embed=embed)

	


@client.command(pass_context = True)
async def setup(ctx, ip, port=25565):
	if ctx.message.author.guild_permissions.administrator == False:
		return await ctx.send("Sorry, you are not a server admin.")

	guild = ctx.guild

	try:
		channel = guild.get_channel(all_status[guild.id][t_ip(ip,port)]["channel"])
		return await ctx.send("Sorry, the McStatus you requested already exists.")
	except:
		pass

	try:
		server = MinecraftServer.lookup("{0}:{1}".format(ip,port))
		status = server.status()
	except:
		return await ctx.send("Sorry, the server {0}:{1} was offline or not found.".format(ip,port))

	category = await ctx.guild.create_category("{0}:{1}".format(ip,port))
	channel = await category.create_voice_channel("Server Online ({0}/{1})".format(status.players.online,status.players.max))

	everyone = guild.get_role(guild.id)
	await channel.set_permissions(everyone, connect=False)

	embed=discord.Embed(title="{0}:{1}".format(ip,port), description="Server Online ({0}/{1})".format(status.players.online,status.players.max), color=0x00ff00)
	embed.set_author(name="Server Status Created")
	await ctx.send(embed=embed)

	save(guild, category, channel, ip, port)



@client.command(pass_context = True)
async def remove(ctx, ip, port=25565):
	if ctx.message.author.guild_permissions.administrator == False:
		return await ctx.send("Sorry, you are not a server admin.")

	guild = ctx.guild

	try:
		channel = guild.get_channel(all_status[guild.id][t_ip(ip,port)]["channel"])
		category = channel.category
	except:
		return await ctx.send("Sorry, the McStatus you requested was not found.")
	
	await channel.delete()
	await category.delete()

	embed=discord.Embed(title="{0}:{1}".format(ip,port), description="Removed {0}:{1}".format(ip,port), color=0xff1a1a)
	embed.set_author(name="Server Status Removed")
	await ctx.send(embed=embed)

	d_remove(guild, ip, port)


	

client.loop.create_task(mcstatusloop())
client.run(token)
