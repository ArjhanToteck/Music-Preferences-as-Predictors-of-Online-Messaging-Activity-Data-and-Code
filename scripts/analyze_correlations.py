import json
import os
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from dotenv import load_dotenv

# load env variables
load_dotenv()

# there has to be at least this many users with the property to calculate correlations with it
MIN_PROPERTY_SAMPLE_SIZE = int(os.getenv("MIN_PROPERTY_SAMPLE_SIZE"))

def main():
	print("Loading data")

	with open("data/messages_data.json", "r") as f:
		message_data = json.load(f)

	with open("data/spotify_data.json", "r") as f:
		music_data = json.load(f)

	df_messages = pd.DataFrame(message_data)
	df_music = pd.DataFrame(music_data)

	# filter for numbers
	messages_numeric_cols = df_messages.select_dtypes(include="number").columns
	music_numeric_cols = df_music.select_dtypes(include="number").columns
	
	print("Merging data by id")

	# merge by id
	merged_data = pd.merge(df_messages, df_music, on="id", how="inner")
	messages_numeric = merged_data[messages_numeric_cols]
	music_numeric = merged_data[music_numeric_cols]

	# drop id column and export to parquet
	unidentifiable_data = merged_data.drop(columns=["id"])

	print("exporting raw data to parquet")	
	unidentifiable_data.to_parquet("data/messages_and_spotify_data.parquet", index=False)

	print("Searching for correlations")

	# get correlation sand save as csvs
	pearson_df = get_correlations(messages_numeric, music_numeric, pearsonr)
	pearson_df.to_parquet("data/pearson_correlations.parquet", index=False)

	print("Correlations computed and saved to files")


def get_correlations(df1, df2, method):
	results = []

	# loop through columns in first property
	for col1 in df1.columns:

		# skip columns with constant values
		if df1[col1].nunique() <= 1:
			continue

		# loop through columns in second property
		for col2 in df2.columns:
			# skip columns with constant values
			if df2[col2].nunique() <= 1:
				continue

			# drop NaN rows
			valid_rows = df1[[col1]].join(df2[[col2]]).dropna()

			if len(valid_rows) < MIN_PROPERTY_SAMPLE_SIZE:
				# skip pairs with small sample size
				continue

			print(f"comparing {col1} with {col2} using {method.__name__}")
	
			# calculate correlation and significance
			correlation, p_value = method(valid_rows[col1], valid_rows[col2])

			results.append({
				"message_metric": col1,
				"music_metric": col2,
				"correlation": correlation,
				"p_value": p_value
			})

	return pd.DataFrame(results)


if __name__ == "__main__":
    main()