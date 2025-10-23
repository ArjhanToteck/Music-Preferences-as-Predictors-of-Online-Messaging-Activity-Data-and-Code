import random
import os
import json
from dotenv import load_dotenv
import discord
from discord import ConnectionType

# load env variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_HISTORY_LIMIT = int(os.getenv("CHANNEL_HISTORY_LIMIT"))
USER_STRATUM_SIZE = int(os.getenv("USER_STRATUM_SIZE"))

class DiscordClient(discord.Client):
	async def on_ready(self):
		print("Logged onto Discord as", self.user)

		# get guild
		guild = self.get_guild(GUILD_ID)
		print(guild)

		# scrape messages and users
		users = await scrape_users(guild)

		# get random sample of users
		spotify_sample = select_random_user_sample(users["spotify_stratum"], USER_STRATUM_SIZE)
		non_spotify_sample = select_random_user_sample(users["non_spotify_stratum"], USER_STRATUM_SIZE)
		
		sample = {
			"spotify_sample": spotify_sample,
			"non_spotify_sample": non_spotify_sample
		}

		# save sample to json
		with open("data/users.json", "w", encoding="utf-8") as f:
			json.dump(sample, f, ensure_ascii=False, indent=2, default=str)
			
		print("User sample data saved to data/users.json")

async def scrape_users(guild):
	users = {
		"spotify_stratum": {},
		"non_spotify_stratum": {},
	}

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
			author = message.author

			# skip bot messages
			if author.bot:
				continue
			
			# check if already in spotify stratum
			if author.id in users["spotify_stratum"]:
				# add new message to list
				users["spotify_stratum"][author.id]["messages"].append(message)

			# check if already in non spotify stratum
			elif author.id in users["non_spotify_stratum"]:
				# add new message to list
				users["non_spotify_stratum"][author.id]["messages"].append(message)


			# new user found
			else:
				# get profile and spotify connection
				spotify_url = None

				try:
					profile = await author.profile()
					connections = profile.connections

					for connection in connections:
						# check if spotify
						if connection.type == ConnectionType.spotify:
							# save url
							spotify_url = connection.url
				except:
					print("failed to fetch profile")

				# create object for user to store messages and user data
				author_data = {
					"user": author,
					"messages": [message],
					"spotifyUrl": spotify_url
				}

				# save user data in appropriate stratum
				if spotify_url == None:
					users["non_spotify_stratum"][author.id] = author_data
				else :
					users["spotify_stratum"][author.id] = author_data

	return users

def select_random_user_sample(users, sample_size):
	# select a random sample of dict keys
	sampled_keys = random.sample(list(users), min(sample_size, len(users)))

	# rebuilds user dict using sampled keys
	sample = {k: users[k] for k in sampled_keys}

	return sample

client = DiscordClient()
client.run(DISCORD_TOKEN)