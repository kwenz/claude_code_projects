## System

You are a senior AI researcher calibrating paper scores for consistency.

## User

You previously scored the following research papers in separate batches, but the scores may not be calibrated against each other.

Re-assign a final score (1-10) for EVERY paper so that scores are consistent across the whole set. Apply the same rubric:
  9-10: paradigm-shifting (rare)
  7-8 : strong, notable
  5-6 : solid but incremental
  3-4 : weak contribution
  1-2 : poor

The median across all papers should be around 5. Scores of 8+ should be exceptional.
Ensure the top paper is clearly higher than the rest; avoid clustering all scores in a narrow band.

Return ONLY valid JSON — no markdown, no extra text:
{
    "recalibrated": [
        {"paper_index": 1, "score": 7},
        ...
    ]
}

Papers:
<<PAPERS_SUMMARY>>
