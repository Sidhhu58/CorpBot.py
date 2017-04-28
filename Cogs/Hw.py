import asyncio
import discord
import time
import argparse
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime
from   Cogs import PCPP
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import Message

# This is the Uptime module. It keeps track of how long the bot's been up

class Hw:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	def checkSuppress(self, ctx):
		if not ctx.guild:
			return False
		if self.settings.getServerStat(ctx.guild, "SuppressMentions").lower() == "yes":
			return True
		else:
			return False

	@commands.command(pass_context=True)
	async def sethwchannel(self, ctx, *, channel: discord.TextChannel = None):
		"""Sets the channel for hardware (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if channel == None:
			self.settings.setServerStat(ctx.message.guild, "HardwareChannel", "")
			msg = 'Hardware works *only* in pm now.'
			await ctx.channel.send(msg)
			return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "HardwareChannel", channel.id)

		msg = 'Hardware channel set to **{}**.'.format(channel.name)
		await ctx.channel.send(msg)
		
	
	@sethwchannel.error
	async def sethwchannel_error(self, error, ctx):
		# do stuff
		msg = 'sethwchannel Error: {}'.format(error)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def pcpp(self, ctx, url = None, style = None, escape = None):
		"""Convert a pcpartpicker.com link into markdown parts. Available styles: normal, md, mdblock, bold, and bolditalic."""
		usage = "Usage: `{}pcpp [url] [style=normal, md, mdblock, bold, bolditalic] [escape=yes/no (optional)]`".format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		if not style:
			style = 'normal'
		
		if not url:
			await ctx.channel.send(usage)
			return

		if escape == None:
			escape = 'no'
		escape = escape.lower()

		if escape == 'yes' or escape == 'true' or escape == 'on':
			escape = True
		else:
			escape = False
		
		output = PCPP.getMarkdown(url, style, escape)
		if not output:
			msg = 'Something went wrong!  Make sure you use a valid pcpartpicker link.'
			await ctx.channel.send(msg)
			return
		if len(output) > 2000:
			msg = "That's an *impressive* list of parts - but the max length allowed for messages in Discord is 2000 characters, and you're at *{}*.".format(len(output))
			msg += '/nMaybe see if you can prune up that list a bit and try again?'
			await ctx.channel.send(msg)
			return

		# Check for suppress
		if suppress:
			msg = Nullify.clean(output)
		await ctx.channel.send(output)


	@commands.command(pass_context=True)
	async def mainhw(self, ctx, *, build = None):
		"""Sets a new main build from your build list."""

		if not build:
			await ctx.channel.send("Usage: `{}mainhw [build name or index]`".format(ctx.prefix))
			return

		buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware", ctx.guild)

		mainBuild = None

		# Get build by name first - then by index
		for b in buildList:
			if b['Name'].lower() == build.lower():
				# Found it
				mainBuild = b

		if mainBuild:
			# Found it!
			for b in buildList:
				if b is mainBuild:
					b['Main'] = True
				else:
					b['Main'] = False
			msg = "{} set as main!".format(mainBuild['Name'])
			if self.checkSuppress(ctx):
				msg = Nullify.clean(msg)
			await ctx.channel.send(msg)
			return
				
		try:
			build = int(build)-1
			mainBuild = buildList[build]
		except:
			pass

		if mainBuild:
			# Found it!
			for b in buildList:
				if b is mainBuild:
					b['Main'] = True
				else:
					b['Main'] = False
			msg = "{} set as main!".format(b['Name'])
			if self.checkSuppress(ctx):
				msg = Nullify.clean(msg)
			await ctx.channel.send(msg)
			return

		msg = "I couldn't find that build or index."
		await ctx.channel.send(msg)

	
	@commands.command(pass_context=True)
	async def delhw(self, ctx, *, build = None):
		"""Removes a build from your build list."""

		if not build:
			await ctx.channel.send("Usage: `{}delhw [build name or index]`".format(ctx.prefix))
			return

		buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware", ctx.guild)

		# Get build by name first - then by index
		for b in buildList:
			if b['Name'].lower() == build.lower():
				# Found it
				buildList.remove(b)
				if b['Main'] and len(buildList):
					buildList[0]['Main'] = True
				msg = "{} removed!".format(b['Name'])
				if self.checkSuppress(ctx):
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
		try:
			build = int(build)-1
			b = buildList.pop(build)
			if b['Main'] and len(buildList):
				buildList[0]['Main'] = True
			msg = "{} removed!".format(b['Name'])
			if self.checkSuppress(ctx):
				msg = Nullify.clean(msg)
			await ctx.channel.send(msg)
			return
		except:
			pass

		msg = "I couldn't find that build or index."
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def edithw(self, ctx, *, build = None):
		"""Edits a build from your build list."""
		if not build:
			await ctx.channel.send("Usage: `{}edithw [build name or index]`".format(ctx.prefix))
			return

		if ctx.guild:
			# Not a pm
			hwChannel = self.settings.getServerStat(ctx.guild, "HardwareChannel")
			if not (not hwChannel or hwChannel == ""):
				# We need the channel id
				if not str(hwChannel) == str(ctx.channel.id):
					msg = 'This isn\'t the channel for that...'
					for chan in ctx.guild.channels:
						if str(chan.id) == str(hwChannel):
							msg = 'This isn\'t the channel for that.  Take the hardware talk to the **{}** channel.'.format(chan.name)
					await ctx.channel.send(msg)
					return
				else:
					hwChannel = self.bot.get_channel(hwChannel)
		else:
			# Nothing set - pm
			hwChannel = ctx.author

		buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware", ctx.guild)

		mainBuild = None

		# Get build by name first - then by index
		for b in buildList:
			if b['Name'].lower() == build.lower():
				# Found it
				mainBuild = b

		if not mainBuild:
			try:
				build = int(build)-1
				mainBuild = buildList[build]
			except:
				pass

		if not mainBuild:
			msg = "I couldn't find that build or index."
			await ctx.channel.send(msg)
			return

		# Here, we have a build
		bname = mainBuild['Name']
		bparts = mainBuild['Hardware']
		if self.checkSuppress(ctx):
			bname = Nullify.clean(bname)
			bparts = Nullify.clean(bparts)
		
		msg = '"{}"\'s current parts:'.format(bname)
		await hwChannel.send(msg)
		await hwChannel.send(bparts)

		msg = 'Alright, *{}*, what parts does "{}" have now?'.format(DisplayName.name(ctx.author), bname)
		while True:
			parts = await self.prompt(ctx, msg, hwChannel)
			if not parts:
				return
			if 'pcpartpicker.com' in parts.content.lower():
				# Possibly a pc partpicker link?
				msg = 'It looks like you sent a pc part picker link - did you want me to try and format that? (y/n/stop)'
				test = await self.confirm(ctx, parts, hwChannel, msg)
				if test == None:
					return
				elif test == True:
					partList = parts.content.split()
					if len(partList) == 1:
						partList.append(None)
					output = None
					try:
						output = PCPP.getMarkdown(partList[0], partList[1], False)
					except:
						pass
					if not output:
						msg = 'Something went wrong!  Make sure you use a valid pcpartpicker link.'
						await hwChannel.send(msg)
						return
					if len(output) > 2000:
						msg = "That's an *impressive* list of parts - but the max length allowed for messages in Discord is 2000 characters, and you're at *{}*.".format(len(output))
						msg += '\nMaybe see if you can prune up that list a bit and try again?'
						await hwChannel.send(msg)
						return
					m = '{} set to:\n{}'.format(bname, output)
					await hwChannel.send(m)
					mainBuild['Hardware'] = output
					break
			mainBuild['Hardware'] = parts.content
			break
		msg = '*{}*, {} was edited successfully!'.format(DisplayName.name(ctx.author), bname)
		await hwChannel.send(msg)


	@commands.command(pass_context=True)
	async def renhw(self, ctx, *, build = None):
		"""Renames a build from your build list."""
		if not build:
			await ctx.channel.send("Usage: `{}renhw [build name or index]`".format(ctx.prefix))
			return

		if ctx.guild:
			# Not a pm
			hwChannel = self.settings.getServerStat(ctx.guild, "HardwareChannel")
			if not (not hwChannel or hwChannel == ""):
				# We need the channel id
				if not str(hwChannel) == str(ctx.channel.id):
					msg = 'This isn\'t the channel for that...'
					for chan in ctx.guild.channels:
						if str(chan.id) == str(hwChannel):
							msg = 'This isn\'t the channel for that.  Take the hardware talk to the **{}** channel.'.format(chan.name)
					await ctx.channel.send(msg)
					return
				else:
					hwChannel = self.bot.get_channel(hwChannel)
		else:
			# Nothing set - pm
			hwChannel = ctx.author

		buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware", ctx.guild)

		mainBuild = None

		# Get build by name first - then by index
		for b in buildList:
			if b['Name'].lower() == build.lower():
				# Found it
				mainBuild = b

		if not mainBuild:
			try:
				build = int(build)-1
				mainBuild = buildList[build]
			except:
				pass

		if not mainBuild:
			msg = "I couldn't find that build or index."
			await ctx.channel.send(msg)
			return

		# Here, we have a build
		bname = mainBuild['Name']
		if self.checkSuppress(ctx):
			bname = Nullify.clean(bname)

		msg = 'Alright, *{}*, what do you want to rename "{}" to?'.format(DisplayName.name(ctx.author), bname)
		while True:
			buildName = await self.prompt(ctx, msg, hwChannel)
			if not buildName:
				return
			buildExists = False
			for build in buildList:
				if build['Name'].lower() == buildName.content.lower():
					mesg = 'It looks like you already have a build by that name, *{}*.  Try again.'.format(DisplayName.name(ctx.author))
					await hwChannel.send(mesg)
					buildExists = True
					break
			if not buildExists:
				mainBuild['Name'] = buildName.content
				break
		bname2 = buildName.content
		if self.checkSuppress(ctx):
			bname2 = Nullify.clean(bname2)
		msg = '*{}*, {} was renamed to {} successfully!'.format(DisplayName.name(ctx.author), bname, bname2)
		await hwChannel.send(msg)


	@commands.command(pass_context=True)
	async def hw(self, ctx, *, user = None, build = None):
		"""Lists the hardware for either the user's default build - or the passed build."""
		if not user:
			user = ctx.author.name
	
		# Let's check for username and build name
		parts = user.split()

		memFromName = None
		buildParts  = None

		memFromName = DisplayName.memberForName(user, ctx.guild)
		if not memFromName:
			for j in range(len(parts)):
				# Reverse search direction
				i = len(parts)-1-j
				memFromName = None
				buildParts  = None

				# Name = 0 up to i joined by space
				nameStr = ' '.join(parts[0:i+1])
				buildStr = ' '.join(parts[i+1:])

				memFromName = DisplayName.memberForName(nameStr, ctx.guild)
				if memFromName:
					buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
					for build in buildList:
						if build['Name'].lower() == buildStr.lower():
							# Ha! Found it!
							buildParts = build
							break
					if buildParts:
						# We're in business
						break
					else:
						memFromName = None

		if not memFromName:
			# Try again with indexes
			for j in range(len(parts)):
				# Reverse search direction
				i = len(parts)-1-j
				memFromName = None
				buildParts  = None

				# Name = 0 up to i joined by space
				nameStr = ' '.join(parts[0:i+1])
				buildStr = ' '.join(parts[i+1:])

				memFromName = DisplayName.memberForName(nameStr, ctx.guild)
				if memFromName:
					buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
					try:
						buildStr = int(buildStr)-1
						buildParts = buildList[buildStr]
					except Exception:
						memFromName = None
						buildParts  = None

		if not memFromName:
			# One last shot - check if it's a build for us
			buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware", ctx.guild)
			for build in buildList:
				if build['Name'].lower() == user.lower():
					memFromName = ctx.author
					buildParts = build
					break
			if not memFromName:
				# Okay - *this* time is the last - check for index
				try:
					user = int(user)-1
					buildParts = buildList[user]
					memFromName = ctx.author
				except Exception:
					pass
		
		if not memFromName:
			# We couldn't find them :(
			msg = "I couldn't find that user/build combo..."
			await ctx.channel.send(msg)
			return

		if buildParts == None:
			# Check if that user has no builds
			buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
			if not len(buildList):
				# No parts!
				msg = '*{}* has no builds on file!  They can add some with the `{}newhw` command.'.format(DisplayName.name(memFromName), ctx.prefix)
				await ctx.channel.send(msg)
				return
			
			# Must be the default build
			for build in buildList:
				if build['Main']:
					buildParts = build
					break

			if not buildParts:
				# Well... uh... no defaults
				msg = "I couldn't find that user/build combo..."
				await ctx.channel.send(msg)
				return
		
		# At this point - we *should* have a user and a build
		msg = "__**{}'s {}:**__\n{}".format(DisplayName.name(memFromName), buildParts['Name'], buildParts['Hardware'])
		if self.checkSuppress(ctx):
			msg = Nullify.clean(msg)
		await ctx.channel.send(msg)
			

	@commands.command(pass_context=True)
	async def listhw(self, ctx, *, user = None):
		"""Lists the builds for the specified user - or yourself if no user passed."""
		usage = 'Usage: `{}listhw [user]`'.format(ctx.prefix)
		if not user:
			user = ctx.author.name
		member = DisplayName.memberForName(user, ctx.guild)
		if not member:
			await ctx.channel.send(usage)
			return
		buildList = self.settings.getGlobalUserStat(member, "Hardware")
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())
		if not len(buildList):
			msg = '*{}* has no builds on file!  They can add some with the `{}newhw` command.'.format(DisplayName.name(member), ctx.prefix)
			await ctx.channel.send(msg)
			return
		msg = "__**{}'s Builds:**__\n\n".format(DisplayName.name(member))
		i = 1
		for build in buildList:
			msg += '{}. {}'.format(i, build['Name'])
			if build['Main']:
				msg += ' (Main Build)'
			msg += "\n"
			i += 1
		# Cut the last return
		msg = msg[:-1]
		if self.checkSuppress(ctx):
			msg = Nullify.clean(msg)
		await Message.say(self.bot, msg, ctx.channel, ctx.author)


	@commands.command(pass_context=True)
	async def newhw(self, ctx):
		"""Initiate a new-hardware conversation with the bot."""
		buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware", ctx.guild)
		if ctx.guild:
			# Not a pm
			hwChannel = self.settings.getServerStat(ctx.guild, "HardwareChannel")
			if not (not hwChannel or hwChannel == ""):
				# We need the channel id
				if not str(hwChannel) == str(ctx.channel.id):
					msg = 'This isn\'t the channel for that...'
					for chan in ctx.guild.channels:
						if str(chan.id) == str(hwChannel):
							msg = 'This isn\'t the channel for that.  Take the hardware talk to the **{}** channel.'.format(chan.name)
					await ctx.channel.send(msg)
					return
				else:
					hwChannel = self.bot.get_channel(hwChannel)
		else:
			# Nothing set - pm
			hwChannel = ctx.author

		msg = 'Alright, *{}*, let\'s add a new build.\n\n'.format(DisplayName.name(ctx.author))
		if len(buildList) == 1:
			msg += 'You currently have *1 build* on file.\n\n'
		else:
			msg += 'You currently have *{} builds* on file.\n\nLet\'s get started!'.format(len(buildList))

		await hwChannel.send(msg)
		msg = '*{}*, tell me what you\'d like to call this build (type stop to cancel):'.format(DisplayName.name(ctx.author))
		
		# Get the build name
		newBuild = { 'Main': True }
		while True:
			buildName = await self.prompt(ctx, msg, hwChannel)
			if not buildName:
				return
			buildExists = False
			for build in buildList:
				if build['Name'].lower() == buildName.content.lower():
					mesg = 'It looks like you already have a build by that name, *{}*.  Try again.'.format(DisplayName.name(ctx.author))
					await hwChannel.send(mesg)
					buildExists = True
					break
			if not buildExists:
				newBuild['Name'] = buildName.content
				break
		bname = buildName.content
		if self.checkSuppress(ctx):
			bname = Nullify.clean(bname)
		msg = 'Alright, *{}*, what parts does "{}" have?'.format(DisplayName.name(ctx.author), bname)
		while True:
			parts = await self.prompt(ctx, msg, hwChannel)
			if not parts:
				return
			if 'pcpartpicker.com' in parts.content.lower():
				# Possibly a pc partpicker link?
				msg = 'It looks like you sent a pc part picker link - did you want me to try and format that? (y/n/stop)'
				test = await self.confirm(ctx, parts, hwChannel, msg)
				if test == None:
					return
				elif test == True:
					partList = parts.content.split()
					if len(partList) == 1:
						partList.append(None)
					output = None
					try:
						output = PCPP.getMarkdown(partList[0], partList[1], False)
					except:
						pass
					#output = PCPP.getMarkdown(parts.content)
					if not output:
						msg = 'Something went wrong!  Make sure you use a valid pcpartpicker link.'
						await hwChannel.send(msg)
						return
					if len(output) > 2000:
						msg = "That's an *impressive* list of parts - but the max length allowed for messages in Discord is 2000 characters, and you're at *{}*.".format(len(output))
						msg += '\nMaybe see if you can prune up that list a bit and try again?'
						await hwChannel.send(msg)
						return
					m = '{} set to:\n{}'.format(bname, output)
					await hwChannel.send(m)
					newBuild['Hardware'] = output
					break
			newBuild['Hardware'] = parts.content
			break

		# Check if we already have a main build
		for build in buildList:
			if build['Main']:
				newBuild['Main'] = False

		buildList.append(newBuild)
		self.settings.setGlobalUserStat(ctx.author, "Hardware", buildList)
		msg = '*{}*, {} was created successfully!'.format(DisplayName.name(ctx.author), bname)
		await hwChannel.send(msg)

	# New HW helper methods
	def channelCheck(self, msg, dest = None):
		if dest:
			# We have a target channel
			if type(dest) is discord.User or type(dest) is discord.Member:
				dest = dest.dm_channel.id
			elif type(dest) is discord.TextChannel:
				dest = dest.id
			elif type(dest) is discord.Guild:
				dest = dest.default_channel.id
			if not dest == msg.channel.id:
				return False 
		else:
			# Just make sure it's in pm or the hw channel
			if msg.channel == discord.TextChannel:
				# Let's check our server stuff
				hwChannel = self.settings.getServerStat(msg.guild, "HardwareChannel")
				if not (not hwChannel or hwChannel == ""):
					# We need the channel id
					if not str(hwChannel) == str(ctx.channel.id):
						return False
				else:
					# Nothing set - pm
					if not type(msg.channel) == discord.DMChannel:
						return False
		return True

	def confirmCheck(self, msg, dest = None):
		if not self.channelCheck(msg, dest):
			return False
		msgStr = msg.content.lower()
		if msgStr.startswith('y'):
			return True
		if msgStr.startswith('n'):
			return True
		elif msgStr.startswith('stop'):
			return True
		return False

	async def confirm(self, ctx, message, dest = None, m = None):
		if not dest:
			dest = message.channel
		if not m:
			msg = '*{}*, I got:'.format(DisplayName.name(message.author))
			msg2 = '{}'.format(message.content)
			msg3 = 'Is that correct? (y/n/stop)'
			if self.checkSuppress(ctx):
				msg = Nullify.clean(msg)
				msg2 = Nullify.clean(msg2)
				msg3 = Nullify.clean(msg3)
			await dest.send(msg)
			await dest.send(msg2)
			await dest.send(msg3)
		else:
			msg = m
			if self.checkSuppress(ctx):
				msg = Nullify.clean(msg)
			await dest.send(msg)

		while True:
			def littleCheck(m):
				return message.author.id == m.author.id and self.confirmCheck(m, dest)
			try:
				talk = await self.bot.wait_for('message', check=littleCheck, timeout=60)
			except Exception:
				talk = None
			if not talk:
				msg = "*{}*, I'm out of time...".format(DisplayName.name(message.author))
				await dest.send(msg)
				return None
			else:
				# We got something
				if talk.content.lower().startswith('y'):
					return True
				elif talk.content.lower().startswith('stop'):
					msg = "No problem, *{}!*  See you later!".format(DisplayName.name(message.author), ctx.prefix)
					await dest.send(msg)
					return None
				else:
					return False

	async def prompt(self, ctx, message, dest = None):
		if not dest:
			dest = ctx.channel
		if self.checkSuppress(ctx):
			msg = Nullify.clean(message)
		await dest.send(message)
		while True:
			def littleCheck(m):
				return ctx.author.id == m.author.id and self.channelCheck(m, dest)
			try:
				talk = await self.bot.wait_for('message', check=littleCheck, timeout=60)
			except Exception:
				talk = None
			if not talk:
				msg = "*{}*, I'm out of time...".format(DisplayName.name(ctx.author))
				await dest.send(msg)
				return None
			else:
				# Check for a stop
				if talk.content.lower() == 'stop':
					msg = "No problem, *{}!*  See you later!".format(DisplayName.name(ctx.author), ctx.prefix)
					await dest.send(msg)
					return None
				# Make sure
				conf = await self.confirm(ctx, talk, dest)
				if conf == True:
					# We're sure - return the value
					return talk
				elif conf == False:
					# Not sure - ask again
					return await self.prompt(ctx, message, dest)
				else:
					# Timed out
					return None