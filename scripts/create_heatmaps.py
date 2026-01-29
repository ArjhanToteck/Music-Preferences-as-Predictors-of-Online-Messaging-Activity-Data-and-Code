import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def main():
	# create heatmaps
	create_correlation_heatmap("data/pearson_correlations.parquet", "Pearson", min_correlation=0.2)


def create_correlation_heatmap(parquet_file, correlation_type, min_correlation=0.2, max_p_value=0.05):
	df = pd.read_parquet(parquet_file)

	# filter for correlation and p value
	if min_correlation is not None:
		df = df[df["correlation"].abs() >= min_correlation]
	if max_p_value is not None:
		df = df[df["p_value"] <= max_p_value]

	# calculate heatmap
	heatmap_data = df.pivot(index="message_metric", columns="music_metric", values="correlation")

	plt.figure(num=f"{correlation_type} Correlations Between Message and Music Variables", figsize=(15, 25))
	plt.xlabel("Music Variables", fontsize=14)
	plt.ylabel("Message Variables", fontsize=14)

	# plot
	ax = sns.heatmap(
		heatmap_data, 
		cmap="coolwarm",
		center=0,
		annot=True,
		linewidths=0.25,
    	linecolor='gray',
		cbar_kws={
			"aspect": 50,
			"label": "Correlation (r)"
		}
	)

	for text in ax.texts:
		text.set_rotation(90)

	plt.tight_layout()
	plt.show()


if __name__ == "__main__":
    main()