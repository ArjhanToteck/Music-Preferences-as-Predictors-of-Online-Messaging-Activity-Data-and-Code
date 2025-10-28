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
	user_stats = {}

	# get playlists
	playlists = get_playlists(spotifyApi, profile_url)
	playlist_lengths = []

	# combine all tracks
	tracks = []
	for playlist in playlists:
		# get tracks from playlist
		print(f"Getting tracks from playlist {playlist['id']}")
		playlist_tracks = get_playlist_tracks(spotifyApi, playlist)

		# add to total tracks list
		tracks.extend(playlist_tracks)

		# count playlist length
		playlist_lengths.append(len(playlist_tracks))

	# get data from combined tracks list
	print("Getting track stats")
	user_stats = get_stats_from_tracks(spotifyApi, tracks)

	# get data on playlist lengths
	user_stats["playlist_length"] = get_distribution_stats(playlist_lengths)

	print(user_stats)


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
	tracks_stats = {
		"track_count": len(tracks)
	}

	# collect audio features for each track from reccobeats
	track_ids = [t["track"]["id"] for t in tracks if t["track"]]
	audio_features = get_audio_features_from_tracks(track_ids)

	# get more properties from spotify metadata
	spotify_metadata = get_metadata_from_tracks(spotifyApi, track_ids)

	# combine audio features and metadata
	all_features = {}

	for f in audio_features:
		if f and f.get("id"):
			all_features[f["id"]] = f
	for m in spotify_metadata:
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
		"explicit",
		"release_year"
	]	

	# loop through properties
	for property in properties:
		# get value of property if applicable
		values = [f[property] for f in all_features.values() if f.get(property) is not None]

		if not values:
			continue

		tracks_stats[property] = get_distribution_stats(values)

	return tracks_stats


def get_audio_features_from_tracks(track_ids):
	audio_features = []

	for i in range(0, len(track_ids), 40):  # batch in 40s
		# get string list of next 40 track ids
		# for some reason they can be None sometimes? maybe local files
		track_batch = [tid for tid in track_ids[i:i+40] if tid is not None]

		ids_batch = ",".join(track_batch)
		
		# get audio features
		url = f"https://api.reccobeats.com/v1/audio-features?ids={ids_batch}"

		response = requests.get(url)
		if response.status_code == 200:
			data = response.json()
			audio_features.extend(data.get("content", []))
		else:
			print(f"https://api.reccobeats.com/v1/audio-features?ids={ids_batch}")
			print(f"Error fetching batch {i}-{i+len(track_batch)}: {response.status_code}")

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


def get_distribution_stats(values):
		# get shape and spread of property in playlist
		values_array = np.array(values)
		return {
			"q1": np.percentile(values_array, 25),
			"median": np.median(values_array),
			"q3": np.percentile(values_array, 75),
			"range": np.ptp(values_array),
			"iqr": np.percentile(values_array, 75) - np.percentile(values_array, 25),
			"std_dev": np.std(values_array),
			"min": np.min(values_array),
			"max": np.max(values_array),
			"mean": np.mean(values_array)
		}


if __name__ == "__main__":
    main()