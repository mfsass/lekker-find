---
trigger: model_decision
description: When running or using a API invloved script, to see if we can optimize api usage trhough batch processing or smarter usage.
---

# Lekker Find Batch Processing & API Rules

This document serves as the source of truth for implementing batch processing and API optimizations for the Lekker Find project. It specifically addresses constraints for reasoning models (like `gpt-5-nano` / `o1`) and the "New" Google Maps Places API.

## 1. OpenAI Batch API (50% Cost Savings)

Use this workflow for strictly non-interactive, background data enrichment tasks (e.g., regenerating descriptions for the entire database). 

**Constraints:**
- **Latency:** 24-hour turnaround window. NOT for realtime user requests.
- **Model Support:** Supports `gpt-3.5-turbo`, `gpt-4o`, `gpt-5-nano` (reasoning models).

### A. JSONL Construction Rule
Input files MUST be valid JSONL (JSON Lines). Each line is a request object.

```json
{"custom_id": "venue-123", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-5-nano", "messages": [...]}}
```

### B. Reasoning Model Config (`gpt-5-nano` / `o1`)
**CRITICAL:** Reasoning models fail if standard parameters are used incorrectly.

| Parameter | Rule | Reason |
| :--- | :--- | :--- |
| **`temperature`** | **MUST BE 1** (or omitted) | Reasoning models do not support variable temperature. Setting to 0 or 0.7 will cause an error (400 Bad Request). |
| **`max_tokens`** | **FORBIDDEN** | Deprecated for reasoning models. |
| **`max_completion_tokens`** | **REQUIRED** | Use this instead. It includes visible output + invisible "reasoning" tokens. Set high (e.g., 5000+) to avoid cutting off thought process. |
| **`top_p`** | **FORBIDDEN** | Not supported. |
| **`system` role** | **RESTRICTED** (Model Dependent) | Some reasoning models demote `system` messages to `user` messages. Check specific model docs if behavior is inconsistent. |

### C. Python Workflow Pattern
Do not implement synchronous waiting. Use a "Submit -> Poll Later" pattern.

```python
# 1. Upload File
file_response = client.files.create(
    file=open("batch_requests.jsonl", "rb"),
    purpose="batch"
)

# 2. Create Batch
batch_response = client.batches.create(
    input_file_id=file_response.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

# 3. Retrieve (Later)
# Check status: client.batches.retrieve(batch_response.id).status
# If 'completed', download output_file_id content.
```

---

## 2. Google Maps Places API (New)

The "New" Places API (v2) has strict billing and optimization requirements.

### A. Field Masking (Mandatory)
You **MUST** specify a Field Mask for every request. Failure to do so results in a 400 error or max-tier billing (if using wildcard `*`).

**Pattern:**
- Header: `X-Goog-FieldMask: places.displayName,places.id,places.formattedAddress`
- **NEVER** use `*` in production.

### B. Cost Optimization (SKUs)
Only request fields in the lowest viable SKU tier.

*   **Basic (Cheap):** `places.id`, `places.displayName`, `places.formattedAddress`, `places.types`, `places.photos`.
*   **Contact (Moderate):** `places.phoneNumber`, `places.websiteUri`.
*   **Atmosphere (Expensive):** `places.editorialSummary`, `places.reviews`, `places.priceLevel`, `places.rating`, `places.userRatingCount`.

**Rule:** By default, only fetch **Basic** fields for discovery. Only fetch **Atmosphere** fields when actively enriching a specific, high-value venue.

---

## 3. Error Handling & Common Pitfalls

1.  **"Context Length Exceeded" with Reasoning Models:**
    *   **Cause:** Reasoning tokens consume the context window invisible to the output.
    *   **Fix:** Ensure input context + `max_completion_tokens` < Model Limit. Reserve at least 25k tokens for reasoning if complex.

2.  **"Invalid Parameter: temperature":**
    *   **Fix:** Hardcode `temperature=1` or remove the key entirely for `gpt-5-nano` calls.

3.  **JSONL Formatting:**
    *   **Fix:** Ensure no trailing commas or newlines break the JSONL structure. Use `json.dump` per line in Python.