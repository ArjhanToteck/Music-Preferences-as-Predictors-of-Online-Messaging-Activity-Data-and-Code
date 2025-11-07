import json
import pandas as pd


def main():
	with open("data/messages_data.json", "r") as f:
		message_data = json.load(f)

	with open("data/spotify_data.json", "r") as f:
		music_data = json.load(f)

	df_messages = pd.DataFrame(message_data)
	df_music = pd.DataFrame(music_data)

	# filter for numbers
	messages_numeric_cols = df_messages.select_dtypes(include="number").columns
	music_numeric_cols = df_music.select_dtypes(include="number").columns
	
	# merge by id
	merged_data = pd.merge(df_messages, df_music, on="id", how="inner")
	messages_numeric = merged_data[messages_numeric_cols]
	music_numeric = merged_data[music_numeric_cols]

	# drop id column and export to csv
	unidentifiable_data = merged_data.drop(columns=["id"])
	unidentifiable_data.to_csv("data/messages_and_spotify_data.csv", index=False)

	# get correlations
	pearson_df = get_correlations(messages_numeric, music_numeric, method="pearson")
	spearman_df = get_correlations(messages_numeric, music_numeric, method="spearman")
	kendall_df = get_correlations(messages_numeric, music_numeric, method="kendall")

	# save as csv
	pearson_df.to_csv("data/pearson_correlations.csv", index=False)
	spearman_df.to_csv("data/spearman_correlations.csv", index=False)
	kendall_df.to_csv("data/kendall_correlations.csv", index=False)

	print("Correlations computed and saved to files")

def get_correlations(df1, df2, method="pearson"):
	results = []

	# loop through columns in first property
	for col1 in df1.columns:

		# loop through columns in second property
		for col2 in df2.columns:
			# skip columns with constant values
			if df1[col1].nunique() <= 1 or df2[col2].nunique() <= 1:
				continue
	
			correlation = df1[col1].corr(df2[col2], method=method)

			results.append({
				"message_metric": col1,
				"music_metric": col2,
				"correlation": correlation
			})

	return pd.DataFrame(results)


if __name__ == "__main__":
    main()