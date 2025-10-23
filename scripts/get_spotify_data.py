import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import numpy as np

# load env variables
load_dotenv()

SPOTIFY_ID = os.getenv("SPOTIFY_ID")
SPOTIFY_SECRET = os.getenv("SPOTIFY_SECRET")
SPOTIFY_PROFILE = os.getenv("SPOTIFY_PROFILE")


def main():
	spotifyApi = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
		client_id=SPOTIFY_ID,
		client_secret=SPOTIFY_SECRET,
	))

	# TODO: do this for all users in users.json automatically
	get_user_data(spotifyApi, SPOTIFY_PROFILE)


def get_user_data(spotifyApi, profile_url):
	playlists = get_playlists(spotifyApi, profile_url)

	playlist_stats = get_playlist_stats(spotifyApi, playlists[0])

	print(playlist_stats)


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


def get_playlist_stats(spotifyApi, playlist):
	playlist_stats = {
		"track_count": playlist["tracks"]["total"]
	}

	# get playlist id
	playlist_id = playlist["id"]
	tracks_data = []

	# get all tracks with pagination from spotify
	results = spotifyApi.playlist_tracks(playlist_id)
	while results:
		tracks_data.extend(results["items"])
		results = spotifyApi.next(results) if results["next"] else None

	# collect audio features for each track from reccobeats
	track_ids = [t["track"]["id"] for t in tracks_data if t["track"]]
	audio_features = []

	for i in range(0, len(track_ids), 100):  # batch in 100s
		# get string list of next 100 track ids
		ids_batch = ",".join(track_ids[i:i+100])
		
		# get audio features
		url = f"https://api.reccobeats.com/v1/audio-features?ids={ids_batch}"

		response = requests.get(url)
		if response.status_code == 200:
			data = response.json()
			audio_features.extend(data.get("content", []))
		else:
			print(f"Error fetching batch {i}-{i+len(ids_batch)}: {response.status_code}")

	# get more properties from spotify metadata
	metadata = []

	for i in range(0, len(track_ids), 50):
		batch = track_ids[i:i+50]
		try:
			results = spotifyApi.tracks(batch)
			for t in results["tracks"]:
				if t:
					metadata.append({
						"id": t["id"],
						"popularity": t["popularity"],
						"explicit": int(t["explicit"]),  # treat as 0/1
						"duration_ms": t["duration_ms"] / 1000  # convert to seconds
					})
		except Exception as e:
			print(f"Error fetching metadata batch {i}-{i+len(batch)}: {e}")

	# combine audio features and metadata
	all_features = {}

	for f in audio_features:
		if f and f.get("id"):
			all_features[f["id"]] = f
	for m in metadata:
		if m and m.get("id"):
			if m["id"] not in all_features:
				all_features[m["id"]] = {}
			all_features[m["id"]].update(m)

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
		"explicit"
	]	

	# loop through properties
	for property in properties:
		# get value of property if applicable
		values = [f[property] for f in all_features.values() if f.get(property) is not None]

		if not values:
			continue
		
		# get shape and spread of property in playlist
		arr = np.array(values)
		playlist_stats[property] = {
			"q1": np.percentile(arr, 25),
			"median": np.median(arr),
			"q3": np.percentile(arr, 75),
			"range": np.ptp(arr),
			"iqr": np.percentile(arr, 75) - np.percentile(arr, 25),
			"std_dev": np.std(arr),
			"min": np.min(arr),
			"max": np.max(arr),
			"mean": np.mean(arr)
		}

	return playlist_stats

if __name__ == "__main__":
    main()