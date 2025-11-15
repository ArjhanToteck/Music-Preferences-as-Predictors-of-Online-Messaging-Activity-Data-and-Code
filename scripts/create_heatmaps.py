import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def main():
	# create heatmaps
	create_correlation_heatmap("data/kendall_correlations.csv", "Kendall", min_correlation=0.15)
	create_correlation_heatmap("data/pearson_correlations.csv", "Pearson", min_correlation=0.2)
	create_correlation_heatmap("data/spearman_correlations.csv", "Spearman", min_correlation=0.2)


def create_correlation_heatmap(file, correlation_type, min_correlation=0.15, max_p_value=0.05):
	df = pd.read_csv(file)

	# filter for correlation and p value
	if min_correlation is not None:
		df = df[df["correlation"].abs() >= min_correlation]
	if max_p_value is not None:
		df = df[df["p_value"] <= max_p_value]

	# calculate heatmap
	heatmap_data = df.pivot(index="message_metric", columns="music_metric", values="correlation")

	plt.figure(num=f"{correlation_type} Correlations Between Message and Music Variables", figsize=(20, 12))

	# plot
	sns.heatmap(
		heatmap_data, 
		cmap="coolwarm",
		center=0,
		annot=False,
		linewidths=0.5
	)

	plt.tight_layout()
	plt.show()


if __name__ == "__main__":
    main()