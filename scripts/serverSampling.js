// how many servers to identify as candidates
// then, a number of them will randomly be selected to be the actual sample
const CANDIDATE_POOL_SIZE = 100;

// how many servers to randomly include in the sample from the candidate pool
const SAMPLE_SIZE = 5;

main();

async function main() {
	// get candidate pool
	const candidatePool = await getCandidatePool(CANDIDATE_POOL_SIZE);
	console.log(`Created candidate pool from the ${CANDIDATE_POOL_SIZE} top servers.`);

	// get sample
	const sample = selectRandomSampleFromCandidatePool(candidatePool, SAMPLE_SIZE);
	console.log(`Created sample of ${SAMPLE_SIZE} random servers.`);

	console.log(sample);
}

async function getCandidatePool(size) {
	// format request query
	const query = `query Entities($input: EntitiesListingParametersInput!) {
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
	}`;

	// format body
	const requestBody = {
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
	};

	// fetch servers from top.gg api
	let response = await fetch("https://api.top.gg/graphql", {
		"headers": {
			"content-type": "application/json",
		},
		"body": JSON.stringify(requestBody),
		"method": "POST",
		"mode": "cors",
		"credentials": "omit"
	});

	let data = await response.json();

	// parse list of servers from data
	const candidateServers = data.data.entitiesV2.nodes;
	return candidateServers;
}

function selectRandomSampleFromCandidatePool(candidatePool, sampleSize, random) {
	// clone candidates list to remove selected servers
	const copy = [...candidatePool];

	const sample = [];

	for (let i = 0; i < sampleSize && copy.length > 0; i++) {
		// get random server
		const index = Math.floor(Math.random() * copy.length);

		// remove from candidates and add to sample
		sample.push(copy.splice(index, 1)[0]);
	}

	return sample;
}