import json
import os
import sys
import time
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import pandas as pd
import numpy as np
from scipy.stats import entropy

# load env variables
load_dotenv()

SPOTIFY_ID = os.getenv("SPOTIFY_ID")
SPOTIFY_SECRET = os.getenv("SPOTIFY_SECRET")
SPOTIFY_PROFILE = os.getenv("SPOTIFY_PROFILE")
SPOTIFY_BATCH_SIZE = int(os.getenv("SPOTIFY_BATCH_SIZE"))

def main():
	spotifyApi = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
		client_id=SPOTIFY_ID,
		client_secret=SPOTIFY_SECRET,
	))

	spotify_data = []
	fetched_users = 0

	# load spotify data from file to pick up where previously left off
	if os.path.exists("data/spotify_data.json"):
		with open("data/spotify_data.json", "r") as progress_file:
			spotify_data = json.load(progress_file)

	# keep track if ids we already checked
	processed_ids = {entry["id"] for entry in spotify_data}

	with open("data/users.json", "r") as users_file:
		servers = json.load(users_file)

		for server in servers:
			spotify_users = server["spotify_sample"]
			for id, user in spotify_users.items():

				# check if already loaded from progress file
				if id in processed_ids:
					continue

				print("getting data from user " + id)

				# get data from profile url
				spotify_url = user["spotifyUrl"]
				user_data = get_user_data(spotifyApi, spotify_url)

				# TODO: don't use id bc thats identifiable
				user_data["has_spotify"] = 1
				user_data["id"] = id

				spotify_data.append(user_data)

				# save data after every spotify user to make sure data isn't lost with errors
				save_spotify_data(spotify_data)

				fetched_users += 1
				check_batch_completion(fetched_users)
			
			# non spotify users
			non_spotify_users = server["non_spotify_sample"]
			
			for id, user in non_spotify_users.items():
				# check if already loaded from progress file
				if id in processed_ids:
					continue

				spotify_data.append({
				# TODO: don't use id bc thats identifiable
					"has_spotify": 0,
					"id": id
				})

				fetched_users += 1
				check_batch_completion(fetched_users)

			# since non spotify users are processed quickly on-device, we can just save once after they're all done
			save_spotify_data(spotify_data)


def save_spotify_data(spotify_data):
	# save data to json
	with open("data/spotify_data.json", "w", encoding="utf-8") as f:
		json.dump(spotify_data, f, ensure_ascii=False, indent=2)


def check_batch_completion(fetched_users):
	# exit program after certain number of users
	if fetched_users >= SPOTIFY_BATCH_SIZE:
		print(f"{SPOTIFY_BATCH_SIZE} users added and saved to file. Wait a bit before the next batch to prevent rate limiting.")
		sys.exit()


def get_user_data(spotifyApi, profile_url):
	user_stats = {}

	# get playlists
	playlists = get_playlists(spotifyApi, profile_url)
	playlist_lengths = []

	# combine all tracks
	all_tracks = []
	for playlist in playlists:
		# get tracks from playlist
		print(f"Getting tracks from playlist {playlist['id']}")
		playlist_tracks = get_playlist_tracks(spotifyApi, playlist)

		# add to total tracks list
		all_tracks.extend(playlist_tracks)

		# count playlist length
		playlist_lengths.append(len(playlist_tracks))

	# skip getting track data from profiles without tracks
	if len(all_tracks) > 0:
		# get data from combined tracks list
		print("Getting track stats")
		user_stats = get_stats_from_tracks(spotifyApi, all_tracks)

		# get data on playlist lengths
		playlist_df = pd.DataFrame({"playlist_length": playlist_lengths})
		user_stats |= get_distribution_from_df(playlist_df, ["playlist_length"])

	# number of tracks and playlists
	user_stats["playlists_count"] = len(playlist_lengths)
	user_stats["tracks_count"] = len(all_tracks)

	return user_stats


def get_playlists (spotifyApi, profile_url):
	# get username from profile link
	username = profile_url.rstrip("/").split("/")[-1]

	# get first page of playlists
	results = spotifyApi.user_playlists(username)

	playlists = []

	# keep going through paginated playlist data
	while results:
		playlists.extend(results["items"])
		results = spotifyApi.next(results) if results["next"] else None
	
	return playlists


def get_playlist_tracks(spotifyApi, playlist):
	# get playlist id
	playlist_id = playlist["id"]
	tracks = []

	# get all tracks with pagination from spotify
	results = spotifyApi.playlist_tracks(playlist_id)
	while results:
		tracks.extend(results["items"])
		results = spotifyApi.next(results) if results["next"] else None

	return tracks


def get_stats_from_tracks(spotifyApi, tracks):
	# collect audio features for each track from reccobeats
	track_ids = [t["track"]["id"] for t in tracks if t["track"]]
	audio_features = get_audio_features_from_tracks(track_ids)

	# get more properties from spotify metadata
	spotify_metadata = get_metadata_from_tracks(spotifyApi, track_ids)

	# create data frames for audio features and metadata
	audio_df = pd.DataFrame(audio_features)
	meta_df = pd.DataFrame(spotify_metadata)

	# merge all features on id
	# it doesn't matter if spotify and reccobeats songs match bc all we need is summary statistics of each individual metric
	all_features_df = pd.concat([audio_df.reset_index(drop=True), meta_df.reset_index(drop=True)], axis=1)

	# properties to analyze
	properties = [
		"acousticness",
		"danceability",
		"energy",
		"liveness",
		"loudness",
		"mode",
		"speechiness",
		"tempo",
		"valence",
		"popularity",
		"duration_ms",
		"explicit",
		"release_year"
	]	

	# get distribution stats
	tracks_stats = get_distribution_from_df(all_features_df, properties)

	# include artist entropy stat
	tracks_stats["artist_entropy"] = get_artist_entropy(tracks)

	return tracks_stats


def get_artist_entropy(tracks):
	# get artists from tracks
	# (only counts the first artist from a track)
	artist_names = [t["track"]["artists"][0]["name"] for t in tracks if t["track"] and t["track"]["artists"]]
	artist_df = pd.DataFrame({"artist_name": artist_names})

	# get counts for each artist
	artist_counts = artist_df["artist_name"].value_counts(normalize=True)  # normalize to get proportions

	# get raw artist entropy
	artist_entropy = entropy(artist_counts)

	# normalize
	unique_artist_count = artist_df["artist_name"].nunique()
	
	if unique_artist_count > 1:
		artist_entropy /= np.log(unique_artist_count)
	else:
		# only one artist, no diversity
		artist_entropy = 0

	return artist_entropy


def get_audio_features_from_tracks(track_ids):
	audio_features = []

	for i in range(0, len(track_ids), 40):  # batch in 40s
		# get string list of next 40 track ids
		# for some reason they can be None sometimes? maybe local files
		track_batch = [tid for tid in track_ids[i:i+40] if tid is not None]

		ids_batch = ",".join(track_batch)

		while True:
			# get audio features
			url = f"https://api.reccobeats.com/v1/audio-features?ids={ids_batch}"
			response = requests.get(url)

			print(f"Fetching tracks {i + 1}-{i + len(track_batch)}")

			if response.status_code == 200:
				data = response.json()
				audio_features.extend(data.get("content", []))
				break  # exit retry loop if successful

			elif response.status_code == 429:
				# handle rate limit
				retry_after = int(response.headers.get("Retry-After", 4)) + 1  # default 5 sec and add an extra second in case
				print(f"Rate limited, retrying after {retry_after} seconds")
				time.sleep(retry_after)

			else:
				print(f"{url}")
				print(f"Error fetching batch {i + 1}-{i+len(track_batch)}: {response.status_code}")
				break  # exit retry loop on other errors

	return audio_features


def get_metadata_from_tracks(spotifyApi, track_ids):
	spotify_metadata = []

	for i in range(0, len(track_ids), 50):
		batch = track_ids[i:i+50]

		# remove None or non strings
		batch = [tid for tid in batch if isinstance(tid, str) and tid.strip()]

		try:
			results = spotifyApi.tracks(batch)
			for track in results["tracks"]:
				if track:
					spotify_metadata.append({
						"id": track["id"],
						"popularity": track["popularity"],
						"explicit": int(track["explicit"]),  # treat as 0/1
						"duration_ms": track["duration_ms"],
						"release_year": int(track["album"]["release_date"][:4])
					})
		except Exception as e:
			print(f"Error fetching metadata batch {i}-{i+len(batch)}: {e}")

	return spotify_metadata


def get_distribution_from_df(df, properties):
	stats = {}

	# apply to each property
	for prop in properties:
		if prop in df.columns:
			stats |= get_distribution_from_col(df[prop], prop)

	return stats


def get_distribution_from_col(col, prefix):
	return {
		prefix + "_q1": float(col.quantile(0.25)),
		prefix + "_median": float(col.median()),
		prefix + "_q3": float(col.quantile(0.75)),
		prefix + "_range": float(col.max() - col.min()),
		prefix + "_iqr": float(col.quantile(0.75) - col.quantile(0.25)),
		prefix + "_std_dev": float(col.std()) if not np.isnan(col.std()) else None,
		prefix + "_min": float(col.min()),
		prefix + "_max": float(col.max()),
		prefix + "_mean": float(col.mean()),
		prefix + "_skewness": float(col.skew()) if not np.isnan(col.skew()) else None
	}


if __name__ == "__main__":
    main()