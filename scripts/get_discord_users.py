import random
import os
import json
from dotenv import load_dotenv
import discord
from discord import Guild, TextChannel

# load env variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_HISTORY_LIMIT = int(os.getenv("CHANNEL_HISTORY_LIMIT"))
USER_SAMPLE_SIZE_PER_SERVER = int(os.getenv("USER_SAMPLE_SIZE_PER_SERVER"))

class DiscordClient(discord.Client):
	async def on_ready(self):
		print("Logged onto Discord as", self.user)

		# get guild
		guild = self.get_guild(GUILD_ID)
		print(guild)

		# scrape messages and users
		users = await scrape_users(guild)

		# get random sample of users
		sample = select_random_user_sample(users, USER_SAMPLE_SIZE_PER_SERVER)

		# save sample to json
		with open("data/users.json", "w", encoding="utf-8") as f:
			json.dump(sample, f, ensure_ascii=False, indent=2, default=str)
			
		print("User sample data saved to data/users.json")

async def scrape_users(guild):
	users = {}

	# get channels list
	channels = await guild.fetch_channels()

	# loop through channels
	for channel in channels:
		# make sure they're readable
		if not channel.permissions_for(guild.me).read_messages:
			continue

		# make sure they're text channels
		if not isinstance(channel, discord.TextChannel):
			continue

		# get message history
		async for message in channel.history(limit=CHANNEL_HISTORY_LIMIT):
			# new user found
			if message.author.id not in users:
				# create object for user to store messages and user data
				users[message.author.id] = {
					"user": message.author,
					"messages": [message]
				}
			else:
				# add new message to list
				users[message.author.id]["messages"].append(message)

	return users

def select_random_user_sample(users, sample_size):
	# select a random sample of dict keys
	sampled_keys = random.sample(list(users), min(sample_size, len(users)))

	# rebuilds user dict using sampled keys
	sample = {k: users[k] for k in sampled_keys}

	return sample

client = DiscordClient()
client.run(DISCORD_TOKEN)