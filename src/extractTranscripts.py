
import pandas as pd
import os
import time
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled
)

BATCH_SIZE = 10
DELAY = 20

ytt_api = YouTubeTranscriptApi()

# Project paths
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_FILE = os.path.join(DATA_DIR, "videos.xlsx")
OUTPUT_FILE = os.path.join(DATA_DIR, "transcripts.xlsx")

# Read input file
df_data = pd.read_excel(INPUT_FILE)

MERGED_FILE = os.path.join(DATA_DIR, "videos_with_transcripts.xlsx")

# Get video IDs from the first column
video_ids = df_data.iloc[:, 0].dropna().astype(str).tolist()

# Load existing transcripts or create a new DataFrame
if os.path.exists(OUTPUT_FILE):
    source_df = pd.read_excel(OUTPUT_FILE)
else:
    source_df = pd.DataFrame(columns=["id", "transcript"])

# Identify videos already saved
if not source_df.empty:
    completed_ids = set(source_df["id"].dropna().astype(str))
else:
    completed_ids = set()

# Select videos not already saved
pending_ids = [
    video_id for video_id in video_ids
    if video_id not in completed_ids
]

batch_ids = pending_ids[:BATCH_SIZE]

print("Videos remaining:", len(pending_ids))
print("Videos in this batch:", len(batch_ids))

for i, video_id in enumerate(batch_ids, start=1):
    print(f"Processing {i}/{len(batch_ids)}: {video_id}")

    try:
        transcript = ytt_api.fetch(video_id)

        transcript_text = " ".join(snippet.text for snippet in transcript)

        new_row = pd.DataFrame([{"id": video_id,"transcript": transcript_text}])

        source_df = pd.concat([source_df, new_row],ignore_index=True)

        print("Transcript fetched successfully.")


    except (NoTranscriptFound, TranscriptsDisabled) as e:
        new_row = pd.DataFrame([{ "id": video_id,"transcript": pd.NA}])
        source_df = pd.concat([source_df, new_row] ,ignore_index=True)
        print(f"Transcript unavailable: {type(e).__name__}")


    except Exception as e:
        print(f"Request failed: {type(e).__name__}: {e}")
        print("Stopping this batch.")
        break

    finally:
        # Save progress in Excel format
        source_df.to_excel(OUTPUT_FILE, index=False)

    # Combine video metadata and transcripts
    merged_df = pd.merge(df_data, source_df, on="id",how="left")

    #convert data frame into excel file
    merged_df.to_excel(MERGED_FILE, index=False)

    if i < len(batch_ids):
        time.sleep(DELAY)

print("Progress saved to:", OUTPUT_FILE)
