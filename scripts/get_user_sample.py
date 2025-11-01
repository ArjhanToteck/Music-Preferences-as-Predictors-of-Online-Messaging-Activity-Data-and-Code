import random
import os
import json
import time
from dotenv import load_dotenv
import discord
from discord import ConnectionType

# load env variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_HISTORY_LIMIT = int(os.getenv("CHANNEL_HISTORY_LIMIT"))
USER_STRATUM_SIZE = int(os.getenv("USER_STRATUM_SIZE"))


def main():
	client = DiscordClient()
	client.run(DISCORD_TOKEN)


class DiscordClient(discord.Client):
	async def on_ready(self):
		print("Logged onto Discord as", self.user)

		await self.scrape_all_servers()


	async def scrape_all_servers(self):
		server_samples = []

		# get all servers
		servers = self.guilds

		for server in servers:
			# fetch server from id
			guild_id = int(server.id)
			guild = self.get_guild(guild_id)

			# scrape server
			server_sample = await scrape_server(guild)
			server_sample["topgg_data"] = server

			server_samples.append(server_sample)

		# save sample to json
		with open("data/users.json", "w", encoding="utf-8") as f:
			json.dump(server_samples, f, ensure_ascii=False, indent=2, default=str)
			
		print("User sample data saved to data/users.json")


async def scrape_server(guild):
		print(f"Scraping server {guild}")

		# scrape messages and users
		users = await scrape_users(guild)

		# get random sample of users
		spotify_sample = select_random_user_sample(users["spotify_stratum"], USER_STRATUM_SIZE)
		non_spotify_sample = select_random_user_sample(users["non_spotify_stratum"], USER_STRATUM_SIZE)
		
		server_sample = {
			"guild": guild,
			"spotify_sample": spotify_sample,
			"non_spotify_sample": non_spotify_sample
		}

		return server_sample


async def scrape_users(guild):
	users = {
		"spotify_stratum": {},
		"non_spotify_stratum": {},
	}

	# keep track of users we failed to fetch so we don't try again
	failed_fetch_users = []

	# get channels list
	channels = await guild.fetch_channels()

	# loop through channels
	for channel in channels:
		# make sure they're writable
		# this avoids announcement channels and shit
		if not channel.permissions_for(guild.me).send_messages:
			continue

		# make sure they're text channels
		if not isinstance(channel, discord.TextChannel):
			continue

		print(f"Scraping channel {channel.name}")

		# get message history
		async for message in channel.history(limit=CHANNEL_HISTORY_LIMIT):
			# TODO: don't store any identifiable data (except for message content)
			author = message.author

			# skip bot messages
			if author.bot:
				continue
			
			# check if already previously checked this user
			if author.id in failed_fetch_users:
				continue
			elif author.id in users["spotify_stratum"]:
				# add new message to list
				users["spotify_stratum"][author.id]["messages"].append(message.content)

			# check if already in non spotify stratum
			elif author.id in users["non_spotify_stratum"]:
				# add new message to list
				users["non_spotify_stratum"][author.id]["messages"].append(message.content)

			# new user found
			else:
				print(f"Found user {author.name}")

				# get profile and spotify connection
				spotify_url = None

				failed_fetch_users.append(author.id)

				try:
					# wait a second so we don't get banned LMAO
					time.sleep(0.5)

					profile = await author.profile()
					connections = profile.connections

					for connection in connections:
						# check if spotify
						if connection.type == ConnectionType.spotify:
							# save url
							spotify_url = connection.url
							print("Found Spotify account")
				except:
					print("Failed to fetch profile")
					continue

				# create object for user to store messages and user data
				author_data = {
					"user": author,
					"messages": [message.content],
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

if __name__ == "__main__":
    main()