# Music Preferences As Predictors of Online Messaging Activity: Data and Code
This is the repository for a research paper that explores the relationships between various variables relating to online music and messaging activity. The paper can be found [here](https://arjhantoteck.vercel.app/projects/musicPreferencesArticle).

This repository contains the Python scripts referenced in the methodology of the paper. The scripts are used to:

1. Create samples of public Discord servers ([get_server_sample.py](scripts/get_server_sample.py)),
2. Create samples of users from among these servers ([get_user_sample.py](scripts/get_user_sample.py)),
3. Analyze the Spotify profiles of these users ([analyze_spotify_profiles.py](scripts/analyze_spotify_profiles.py)),
4. Analyze the Discord messaging activity of these users ([analyze_messages.py](scripts/analyze_messages.py)),
5. Calculate correlations ([analyze_correlations.py](scripts/analyze_correlations.py)), and
6. Create heatmaps of these correlations ([create_heatmaps.py](scripts/create_heatmaps.py))

This repository also contains the raw data referenced in the results of the paper. The data is available in the [published_data](published_data) folder. It was obtained through the steps discussed in the methodology of the paper.

# Environment Variables
Some environment variables must be set to run the scripts, which should be done in .env at the root of the repository. The environment variables used are as follows:

- DISCORD_TOKEN: The Discord user token which is used to scrape message data and Spotify profile URLs.
- SERVER_CANDIDATE_POOL_SIZE: The number of servers to fetch from Top.gg, from which a random sample of servers will be picked. The study used a value of 1000.
- SERVER_SAMPLE_SIZE: The servers to randomly sample from the fetched server pool. The study used a value of 50.
- USER_STRATUM_SIZE: From each server, two strata are created: one for users with Spotify accounts and one for users without Spotify accounts. The number of users per stratum is defined by this variable. The study used a value of 50.
- CHANNEL_HISTORY_LIMIT: To sample users from a server, the script searches through the most recent messages in each channel. This variable defines how many recent messages from each channel should be fetched. The study used a value of 2000.
- SPOTIFY_ID: The ID for the Spotify API, which is used to scrape music data from Spotify.
- SPOTIFY_SECRET: The secret for the Spotify API, which is used to scrape music data from Spotify.
- SPOTIFY_BATCH_SIZE: The script fetches Spotify user data in batches to avoid rate limiting or account banning. This variable defines the number of users to be fetched per batch. The study used a value of 300.
- MIN_PROPERTY_SAMPLE_SIZE: When calculating correlations between metrics, any metric with less than a specific number of is was not calculated, as it would be unlikely to yield meaningful results. This variable defines the minimum number of users that must be met to consider a variable in the correlations. The study used a value of 250.

# Dependencies
For accurate reproducibility, it is important to install the following Python dependencies with the following versions:

- [alt-profanity-check](https://github.com/dimitrismistriotis/alt-profanity-check), version 1.7.2
- [discord.py-self](https://github.com/dolfies/discord.py-self), version 2.1.0b5180+g600fd36d
- [matplotlib](https://matplotlib.org/), version 3.5.1
- [numpy](https://numpy.org/), version  1.26.4
- [pandas](https://pandas.pydata.org/), version 2.2.1
- [python-dotenv](https://pypi.org/project/python-dotenv/), version 1.2.1
- [scipy](https://scipy.org/), version 1.8.0
- [seaborn](https://seaborn.pydata.org/), version 0.13.2
- [spotipy](https://github.com/spotipy-dev/spotipy), version 2.25.1
- [textblob](https://github.com/sloria/textblob), version 0.19.0
- [textstat](https://textstat.org/), version  0.7.10
- [vaderSentiment](https://github.com/cjhutto/vaderSentiment), version 3.3.2
