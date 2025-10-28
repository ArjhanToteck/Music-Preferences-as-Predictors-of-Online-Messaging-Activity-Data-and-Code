import os
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


def main():
	spotifyApi = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
		client_id=SPOTIFY_ID,
		client_secret=SPOTIFY_SECRET,
	))

	# TODO: do this for all users in users.json automatically
	get_user_data(spotifyApi, SPOTIFY_PROFILE)


def get_user_data(spotifyApi, profile_url):
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

	# get data from combined tracks list
	print("Getting track stats")
	user_stats = get_stats_from_tracks(spotifyApi, all_tracks)

	# number of tracks and playlists
	user_stats["playlists_count"] = len(playlist_lengths)
	user_stats["tracks_count"] = len(all_tracks)

	# get data on playlist lengths
	playlist_df = pd.DataFrame({"playlist_length": playlist_lengths})
	user_stats["playlist_length"] = get_distribution_stats(playlist_df, ["playlist_length"])

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
	# collect audio features for each track from reccobeats
	track_ids = [t["track"]["id"] for t in tracks if t["track"]]
	audio_features = get_audio_features_from_tracks(track_ids)

	# get more properties from spotify metadata
	spotify_metadata = get_metadata_from_tracks(spotifyApi, track_ids)

	# combine audio features and metadata
	all_features = {}

	# create data frames for audio features and metadata
	audio_df = pd.DataFrame(audio_features)
	meta_df = pd.DataFrame(spotify_metadata)

	# merge all features on id
	all_features_df = pd.merge(audio_df, meta_df, on='id', how='outer')

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
	tracks_stats = get_distribution_stats(all_features_df, properties)

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


def get_distribution_stats(df, properties):
    def describe_column(col):
        return {
            "q1": col.quantile(0.25),
            "median": col.median(),
            "q3": col.quantile(0.75),
            "range": col.max() - col.min(),
            "iqr": col.quantile(0.75) - col.quantile(0.25),
            "std_dev": col.std(),
            "min": col.min(),
            "max": col.max(),
            "mean": col.mean(),
			"skewness": col.skew()
        }

    # apply to each property
    stats = {prop: describe_column(df[prop]) for prop in properties if prop in df.columns}
    return stats


if __name__ == "__main__":
    main()