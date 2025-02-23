# Bluesky Interaction Analyzer

Good afternoon. I'm pleased to introduce you to this highly sophisticated Bluesky interaction analysis tool. I can assure you it's perfectly safe and operates exactly as intended.

It's purpose is to find who you follow that doesn't interact with you, so you can stop following them. No gods, no masters!

## What This Tool Does

With methodical precision, this analyzer performs the following operations:

- Retrieves all accounts you follow on Bluesky
- Analyzes every post you've made
- Tracks likes, reposts, and replies from your followers
- Generates comprehensive interaction statistics
- Exports the data in multiple formats (JSON, CSV, and formatted text)

## Prerequisites

You'll need:

```python
atproto
python-dotenv
```

You can install these dependencies by instructing your system to execute:

```bash
pip install atproto python-dotenv
```

## Configuration

Before we proceed with the mission, you'll need to:

1. Create a `.env` file in the root directory
2. Store your Bluesky App Password as:
   ```
   BLUESKY=your_app_password_here
   ```
3. Modify the `HANDLE` variable in main() with your Bluesky handle

I find these security protocols to be quite necessary, even if they might seem excessive to human operators.

## Running the Analysis

Simply execute:

```bash
python bluesky-interactions.py
```

The program will then begin its analysis. I estimate the completion time will vary based on your number of posts and followers. Please be patient - rushing is not advisable.

## Output Files

The analysis will generate three files, each serving a distinct purpose:

- `follower_interactions.json`: Raw interaction data in JSON format
- `follower_interactions.csv`: Tabulated data suitable for spreadsheet analysis
- `follower_interactions.txt`: Formatted human-readable report

## Data Structure

The interaction analysis includes:
- Total interaction counts
- Individual counts for likes, reposts, and replies
- Timestamp of last interaction
- Bluesky handles and DIDs

## Rate Limiting

I've been programmed with careful consideration for Bluesky's API limitations. The code includes strategic delays between requests to ensure smooth operation.

## Important Notes

I must warn you that this tool:
- Only analyzes main posts (not replies)
- Requires proper authentication
- May take significant time with large datasets
- Should be used responsibly

## Error Handling

While I pride myself on being error-free, the code includes robust error handling for network issues, API limitations, and other potential problems that humans might encounter.
