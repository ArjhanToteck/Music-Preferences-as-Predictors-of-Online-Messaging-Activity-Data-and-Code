# Music Preferences As Predictors of Online Messaging Activity
This is the repository for a research paper that explores the relationships between various variables relating to online music and messaging activity.

This repository contains the Python scripts referenced in the methodology of the paper. The scripts are used to:

1. Create samples of public Discord servers ([get_server_sample.py](scripts/get_server_sample.py)),
2. Create samples of users from among these servers ([get_user_sample.py](scripts/get_user_sample.py)),
3. Analyze the Spotify profiles of these users ([analyze_spotify_profiles.py](scripts/analyze_spotify_profiles.py)),
4. Analyze the Discord messaging activity of these users ([analyze_messages.py](scripts/analyze_messages.py)),
5. Calculate correlations ([analyze_correlations.py](scripts/analyze_correlations.py)), and
6. Create heatmaps of these correlations ([create_heatmaps.py](scripts/create_heatmaps.py))

This repository also contains the raw data referenced in the results of the paper. The data is available in the [published_data](published_data) folder. It was obtained through the steps discussed in the methodology of the paper.

# Dependencies
For accurate reproducibility, it is important to install the following Python dependencies with the following versions:

- [alt-profanity-check](https://github.com/dimitrismistriotis/alt-profanity-check), version 1.7.2
- [discord.py-self](https://github.com/dolfies/discord.py-self), version  2.1.0
- [matplotlib](https://matplotlib.org/), version  3.5.1
- [numpy](https://numpy.org/), version  1.26.4
- [pandas](https://pandas.pydata.org/), version  2.2.1
- [scipy](https://scipy.org/), version  1.8.0
- [seaborn](https://seaborn.pydata.org/), version  0.13.2
- [spotipy](https://github.com/spotipy-dev/spotipy), version  2.25.1
- [textblob](https://github.com/sloria/textblob), version  0.19.0
- [textstat](https://textstat.org/), version  0.7.10
- [vaderSentiment](https://github.com/cjhutto/vaderSentiment), version  3.3.2