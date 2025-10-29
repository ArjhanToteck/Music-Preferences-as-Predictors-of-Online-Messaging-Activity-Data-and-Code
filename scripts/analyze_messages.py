from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import textstat
from profanity_check import predict_prob as predict_profanity_prob
from textblob import TextBlob
from collections import Counter
import pandas as pd

vaderSentimentAnalyzer = SentimentIntensityAnalyzer()

def main():
	print(analyze_user(["i fucjkijnhg hate you and want you to die", "I love you; I want you to live!! 😍"]))


def analyze_user(messages):
    # analyze_message on every message
    results = [analyze_message(msg) for msg in messages]

    # flatten nested dictionaries
    def flatten_dict(d, parent_key=''):
        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}_{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(flatten_dict(v, new_key))
            elif isinstance(v, (list, pd.Series)):
                # Skip lists/arrays or convert to scalar if needed
                items[new_key] = v[0] if isinstance(v, (list, pd.Series)) else v
            else:
                items[new_key] = v
        return items

    flat_results = [flatten_dict(r) for r in results]
    df = pd.DataFrame(flat_results)

    # get statistics for columns
    stats = {
		"message_count": len(messages)
	}
    for col_name, col in df.items():
        if pd.api.types.is_numeric_dtype(col):
            stats[col_name] = {
                "q1": col.quantile(0.25),
                "median": col.median(),
                "q3": col.quantile(0.75),
                "range": col.max() - col.min(),
                "iqr": col.quantile(0.75) - col.quantile(0.25),
                "std_dev": col.std(),
                "min": col.min(),
                "max": col.max(),
                "mean": col.mean(),
                "skewness": col.skew(),
            }

    return stats


def analyze_message(message):
	data = {}
	
	data["vader_polarity_data"] = vaderSentimentAnalyzer.polarity_scores(message)
	data["textstat_data"] = get_textstat_data(message)
	data["textblob_data"] = get_textblob_data(message)
	data["profanity_probability"] = predict_profanity_prob([message])
	data["uppercase_ratio"] = get_uppercase_ratio(message)
	data["alpha_ratio"] = get_alpha_ratio(message)
	data["ascii_ratio"] = get_ascii_ratio(message)

	return data


def get_textstat_data(message):
	word_count = message.split()

	return {
		"flesch_reading_ease": textstat.flesch_reading_ease(message),
		"flesch_kincaid_grade": textstat.flesch_kincaid_grade(message),
		"smog_index": textstat.smog_index(message),
		"coleman_liau_index": textstat.coleman_liau_index(message),
		"automated_readability_index": textstat.automated_readability_index(message),
		"dale_chall_readability_score": textstat.dale_chall_readability_score(message),

		# we want a ratio of difficult words to all words, not just a count
		"difficult_word_ratio": textstat.difficult_words(message) / textstat.lexicon_count(message, removepunct=True),

		"linsear_write_formula": textstat.linsear_write_formula(message),
		"gunning_fog": textstat.gunning_fog(message)
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

	# get counts for each part of speech
	pos_counts = Counter(tag for _, tag in tags)

	# get ratio for each part of speech
	pos_ratios = {pos: count / word_count for pos, count in pos_counts.items()} if word_count else {}


	data = {
		"word_count": word_count,
		"sentence_count": len(message_blob.sentences),
		"polarity": message_blob.sentiment.polarity,
		"subjectivity": message_blob.sentiment.subjectivity,
		"pos_ratios": pos_ratios
	}

	return data

if __name__ == "__main__":
    main()