import requests
import random
import json

import os
from dotenv import load_dotenv

# load env variables
load_dotenv()

# how many servers to identify as candidates
# then, a number of them will randomly be selected to be the actual sample
SERVER_CANDIDATE_POOL_SIZE = int(os.getenv("SERVER_CANDIDATE_POOL_SIZE"))

# how many servers to randomly include in the sample from the candidate pool
SERVER_SAMPLE_SIZE = int(os.getenv("SERVER_SAMPLE_SIZE"))

def main():
    # get candidate pool
    candidate_pool = get_candidate_pool(SERVER_CANDIDATE_POOL_SIZE)
    print(f"Created candidate pool from the {SERVER_CANDIDATE_POOL_SIZE} top servers.")

    # get sample
    sample = select_random_sample_from_candidate_pool(candidate_pool, SERVER_SAMPLE_SIZE)
    print(f"Created sample of {SERVER_SAMPLE_SIZE} random servers.")

    # save sample to json
    with open("data/servers.json", "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
        
    print("Server sample data saved to data/servers.json")

def get_candidate_pool(size):
    # format request query
    query = """
    query Entities($input: EntitiesListingParametersInput!) {
        entitiesV2(input: $input) {
            nodes {
                ...EntityItem
            }
        }
    }

    fragment MinimalEntity on Entity {
        __typename
        id: externalId
        internalId: id
        type
        platform
        name
        iconUrl
        shortDescription
    }

    fragment EntityItem on Entity {
        ...MinimalEntity
        icon
        votes
        nsfwLevel
        tags {
            slug
            displayName
        }
        socialCount
        createdAt
        reviewStatus
        reviewStats {
            averageScore
            reviewCount
            scoreDistribution {
                key
                value
            }
        }
        ... on DiscordBot {
            watcherMetadata {
                invitedAt
                invitedBy
            }
        }
        ... on DiscordServer {
            inviteCode
            serverTag {
                slug
                iconUrl
            }
        }
    }
    """

    # format body
    request_body = {
        "query": query,
        "variables": {
            "input": {
                "limit": size,
                "skip": 0,
                "sortOrder": "TOTAL_SIZE",
                "tagSlugs": [],
                "languageCodes": [],
                "reviewScore": {},
                "discordServer": {},
                "type": "SERVER",
                "platform": "DISCORD"
            }
        },
        "operationName": "Entities"
    }

    # fetch servers from top.gg api
    response = requests.post(
        "https://api.top.gg/graphql",
        json=request_body,
        headers={"content-type": "application/json"}
    )
    
    data = response.json()

    # parse list of servers from data
    candidate_servers = data["data"]["entitiesV2"]["nodes"]
    return candidate_servers

def select_random_sample_from_candidate_pool(candidate_pool, sample_size):
    # select a random sample
    return random.sample(candidate_pool, min(sample_size, len(candidate_pool)))

if __name__ == "__main__":
    main()