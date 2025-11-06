import json
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import textstat
from profanity_check import predict_prob as predict_profanity_prob
from textblob import TextBlob
from collections import Counter
import pandas as pd

vaderSentimentAnalyzer = SentimentIntensityAnalyzer()

def main():
	message_data = []

	# TODO: use csv instead of json
	with open("data/users.json", "r") as file:
		servers = json.load(file)

		for server in servers:
			# go through both spotify and non spotify users
			users = server["spotify_sample"] | server["non_spotify_sample"]

			for id, user in users.items():
				print("getting data from user " + id)
				messages = user["messages"]
				user_data = analyze_user(messages)

				# TODO: don't use id bc thats identifiable
				user_data["id"] = id

				message_data.append(user_data)

	# save data to json
	# TODO: use csv instead of json
	with open("data/messages_data.json", "w", encoding="utf-8") as f:
		json.dump(message_data, f, ensure_ascii=False, indent=2)


def analyze_user(messages):
	# analyze_message on every message
	message_data = [analyze_message(msg) for msg in messages]

	df = pd.DataFrame(message_data)

	# get statistics for columns
	stats = {
		"message_count": len(messages)
	}
	
	for col_name, col in df.items():
		if pd.api.types.is_numeric_dtype(col):
			stats[col_name + "_q1"] = float(col.quantile(0.25))
			stats[col_name + "_median"] = float(col.median())
			stats[col_name + "_q3"] = float(col.quantile(0.75))
			stats[col_name + "_range"] = float(col.max() - col.min())
			stats[col_name + "_iqr"] = float(col.quantile(0.75) - col.quantile(0.25))
			stats[col_name + "_std_dev"] = float(col.std()) if not np.isnan(col.std()) else None
			stats[col_name + "_min"] = float(col.min())
			stats[col_name + "_max"] = float(col.max())
			stats[col_name + "_mean"] = float(col.mean())
			stats[col_name + "_skewness"] = float(col.skew()) if not np.isnan(col.skew()) else None

	return stats


# TODO: add discord specific metrics like custom emojis, mentions, attachments, and links
def analyze_message(message):
	data = {}
	
	data |= get_polarity_scores(message)
	data |= get_textstat_data(message)
	data |= get_textblob_data(message)

	data["profanity_probability"] = predict_profanity_prob([message])[0]
	data["uppercase_ratio"] = get_uppercase_ratio(message)
	data["alpha_ratio"] = get_alpha_ratio(message)
	data["ascii_ratio"] = get_ascii_ratio(message)

	return data


def get_polarity_scores(message):
	polarity_scores = vaderSentimentAnalyzer.polarity_scores(message)


	return {
		"vader_negative": polarity_scores["neg"],
		"vader_neutral": polarity_scores["neu"],
		"vader_positive": polarity_scores["pos"],
		"vader_compound": polarity_scores["compound"]
	}


def get_textstat_data(message):
	word_count = textstat.lexicon_count(message, removepunct=True)

	difficult_word_ratio = 0
	
	if word_count > 0:
		# we want a ratio of difficult words to all words, not just a count
		difficult_word_ratio = textstat.difficult_words(message) / word_count

	return {
		"textstat_flesch_reading_ease": textstat.flesch_reading_ease(message),
		"textstat_flesch_kincaid_grade": textstat.flesch_kincaid_grade(message),
		"textstat_smog_index": textstat.smog_index(message),
		"textstat_coleman_liau_index": textstat.coleman_liau_index(message),
		"textstat_automated_readability_index": textstat.automated_readability_index(message),
		"textstat_dale_chall_readability_score": textstat.dale_chall_readability_score(message),
		"textstat_difficult_word_ratio": difficult_word_ratio,
		"textstat_linsear_write_formula": textstat.linsear_write_formula(message),
		"textstat_gunning_fog": textstat.gunning_fog(message)
	}


def get_uppercase_ratio(message):
	# get letters
	letters = [c for c in message if c.isalpha()]

	# skip if no letters
	if not letters:
		return 0.0

	# get uppercase letters
	upper_count = sum(1 for c in letters if c.isupper())

	# return ratio of uppercase letters to total letters
	return upper_count / len(letters)


def get_alpha_ratio(message):
	# get letters
	letters = [c for c in message if c.isalpha()]

	# skip if no letters
	if not letters:
		return 0.0

	# return ratio of letters to total characters
	return  len(letters) / len(message)


def get_ascii_ratio(message):
	# get ascii chars
	ascii = [c for c in message if c.isascii()]


	# skip if no ascii
	if not ascii:
		return 0.0

	# return ratio of letters to total characters
	return  len(ascii) / len(message)


def get_textblob_data(message):

	message_blob = TextBlob(message)
	tags = message_blob.tags
	word_count = len(tags)


	data = {
		"textblob_word_count": word_count,
		"textblob_sentence_count": len(message_blob.sentences),
		"textblob_polarity": message_blob.sentiment.polarity,
		"textblob_subjectivity": message_blob.sentiment.subjectivity
	}

		# get counts for each part of speech
	pos_counts = Counter(tag for _, tag in tags)

	# get ratio for each part of speech
	pos_ratios = {f"textblob_{pos}_ratio": count / word_count for pos, count in pos_counts.items()} if word_count else {}

	data |= pos_ratios

	return data

if __name__ == "__main__":
    main()