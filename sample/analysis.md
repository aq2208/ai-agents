# Sample Notebooks Analysis

Analysis of `main.ipynb` and `discovery_data 1.ipynb` — both relate to ZaloPay AI customer support workflows.

---

## 1. `main.ipynb` — AI Ticket Resolution Audit

### What It Does

This notebook audits the output of ZaloPay's AI support system. The AI receives incoming support tickets, attempts to auto-resolve them via rule matching, and either resolves them (`ai_resolved`) or escalates to human CS (`cs_escalated`). This notebook inspects that output data to understand what happened and why.

### Data Sources

**Primary dataset** — loaded from a JSON API (commented out at the top) and later from a CSV:
```
43001619004_tickets-June-05-2026-03_24.csv
```
This is a ZaloPay Freshdesk CSV export. 1,754 rows, 16 columns.

**Secondary enrichment** — Freshdesk REST API (`vngzalopay.freshdesk.com`) is queried ticket-by-ticket to retrieve full conversation history.

### Schema

| Column | Description |
|--------|-------------|
| `id` | Internal AI system ticket ID |
| `freshdesk_id` | Freshdesk ticket ID (external) |
| `transid` | ZaloPay transaction ID (0 if not a transaction complaint) |
| `source_endpoint` | Which AI endpoint handled it — `process-async-promotion` or `process-async` |
| `is_matched` | Whether the AI found a matching rule for this ticket |
| `matched_rule` | Which rule matched (e.g. `Rule #2 - 5: collection_12137_response_status...`) |
| `processing_time_ms` | End-to-end latency of the AI pipeline |
| `timing_steps` | Step-by-step timing breakdown (JSON array) |
| `message` | Raw HTML response template selected by the rule engine |
| `refine_message` | LLM-refined version of the message (personalized Vietnamese text) |
| `created_at` | ISO 8601 timestamp |
| `iteration_count` | How many AI iterations were used: 0 = first pass resolved, 1 = had to retry |
| `conversation_state` | `completed` or `cs` (escalated to customer service) |
| `ticket_status` | `ai_resolved` or `cs_escalated` |
| `langfuse_trace_url` | Link to Langfuse trace for debugging the LLM call |
| `comments` | Conversation history (user/admin/AI messages as JSON array) |

### Key Observations

#### Two Source Endpoints

```
process-async-promotion  →  Promotion/voucher complaints
process-async            →  General complaints (transfers, errors, etc.)
```

The ticket schema and timing_steps differ between them. Promotion tickets go through a rule engine (`get_collections` step), while general tickets go through `refine_messages`.

#### The Fallback Escalation Pattern

The notebook specifically investigates tickets where `is_matched=False`, which produce a default fallback message:

> *"Yêu cầu của bạn đã được gửi đến nhân viên chăm sóc khách hàng. Vui lòng chờ trong giây lát..."*

These 19 tickets (in the shown sample) all have:
- `ticket_status = cs_escalated`
- `conversation_state = cs`
- `iteration_count = 0` — the AI gave up immediately without retrying
- Empty `timing_steps = []` — no processing steps ran at all

This suggests these tickets failed very early (before any rule matching) — possibly due to missing/invalid input or an unrecognized ticket category.

#### Freshdesk API Fetch

```python
for i in ticket_id:
    url = f"https://vngzalopay.freshdesk.com/api/v2/tickets/{i}?include=conversations"
    response = requests.get(url, auth=HTTPBasicAuth(api_key, "X"))
    time.sleep(1)  # rate limiting: 1 req/sec
```

The notebook fetches 2,268 tickets (not all in the shown sample — this is from a separate run). The `JSONDecodeError` that appears was a one-time error: the API returned an empty body for one ticket (likely rate-limited or the ticket was deleted). The script had no error handling, so it halted. The final `len(response_list) = 2268` confirms the fetch ultimately completed successfully.

#### `map_ticket_to_payload()` — Key Parsing Logic

This function normalizes Freshdesk's raw ticket format into a flat payload:

1. **Parses description text** — splits `+ Key: Value` lines into a dict (including nested "Thông tin thêm" sub-fields)
2. **Filters conversations** — maps Freshdesk category codes to roles:
   - `category=1` → `user`
   - `category=3` → `admin`
   - `user_id=43083493613` → `AI` (hardcoded AI agent user ID)
   - Skips private/internal notes
3. **Extracts TransID and UserID** — from both custom fields and parsed description

### Issues / Gaps

| Issue | Detail |
|-------|--------|
| No error handling in API loop | `response.json()` crashes on empty response — should check `response.status_code` first |
| Hardcoded AI user ID | `43083493613` — will break silently if the AI agent account changes |
| `extract_problem()` has a bug | References `des` instead of `description_json` (undefined variable) — this function would error at runtime |
| API key exposed in notebook | `api_key = "Otm4mt5dMrvZZ3m5ut"` is hardcoded in a cell — should use environment variable |
| Rate limiting via `time.sleep(1)` | Brittle — Freshdesk's rate limit is per-account (300 req/min on paid plans), so 1 req/sec is conservative but doesn't handle 429 responses |

### Output

```python
pd.DataFrame(response_list).to_excel('check_2.xlsx', index=False)
```

Also exports a per-ticket view showing the first two messages in each conversation (role + content), useful for manually reviewing what the AI sent vs. what the user replied.

---

## 2. `discovery_data 1.ipynb` — IBFT Ticket Deduplication for Labeling

### What It Does

This notebook selects a **diverse, representative sample** of Inter-Bank Fund Transfer (IBFT) tickets from a large labeled dataset. The goal is to find tickets that are semantically distinct from each other — useful for creating a high-quality evaluation set or training data without redundant examples.

### Data Source

```
tickets_20260604_150859_with_labels.csv
```

A large labeled ticket export. Has mixed-type columns 21 and 22 (triggers a pandas `DtypeWarning` — these columns likely contain both numeric IDs and string values and should be read with `dtype=str` or `low_memory=False`).

### Filtering

Filters to a single issue category:
```python
df[df["cf_i_tc145665"] == "241 - Chuyển Tiền ATM"]
```

`cf_i_tc145665` is a Freshdesk custom field — this filters to ATM money transfer tickets specifically, as opposed to card payments, QR code payments, etc.

Also drops rows with any null values across the selected columns and resets the index.

### Feature Engineering

Three preprocessing steps build the `classify_context` field used for embedding:

**1. Remove transaction IDs (`remove_transaction_info`)**

Strips PII and noise before embedding:
```
(Mã giao dịch: 260501002782075) - (Ticket id: 6808289)  →  removed
260501002782075  (15-digit standalone number)  →  removed
```

This prevents the embedding model from treating different transaction IDs as different text — the transaction ID itself carries no semantic meaning for classification.

**2. Parse description text (`parse_description_text`)**

Freshdesk description fields use a `+ Key: Value` format. This splits them into a structured dict for selective extraction.

**3. Extract problem fields (`extract_problem`)**

Selects only the semantically meaningful fields for classification:
```
Mục đích chuyển tiền   (Purpose of the transfer)
Có liên hệ người nhận chưa  (Has the sender contacted the recipient?)
Mô tả  (Free-text description of the problem)
```

Combined into `classify_context = "Tiêu đề: {subject}\n{problem}"`.

**Note:** There is a bug in `extract_problem` — it iterates over `des.items()` but `des` is undefined in that scope. Should be `description_json.items()`. This will raise a `NameError` at runtime if called directly; in the notebook it may work because a variable named `des` existed in a prior cell's scope.

### Embedding Model

```python
model = SentenceTransformer("google/gemma-3-270m")
```

`google/gemma-3-270m` is a **language model**, not a sentence embedding model. Using it with SentenceTransformer causes all transformer weights to be randomly initialized (as shown by the extensive "newly initialized" warning in the output). This means the embeddings are **random vectors**, not meaningful semantic representations.

The deduplication still "works" in that cosine similarity on random vectors will rarely exceed 0.85, so most tickets will be kept as "unique" — but this is not filtering by semantic similarity, it's filtering by chance. The 197 selected samples likely reflect near-uniform sampling rather than true semantic deduplication.

**Better alternatives:**
```python
# Multilingual sentence embedding — actually designed for this
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Vietnamese-specific
model = SentenceTransformer("keepitreal/vietnamese-sbert")

# If already using PhoBERT elsewhere
model = SentenceTransformer("VoVanPhuc/sup-SimCSE-VietNamese-phobert-base")
```

### Deduplication Algorithm

```python
for each ticket:
    embed the classify_context
    compute cosine similarity against all already-selected embeddings
    if max_similarity < 0.85:
        add to selected set
```

This is a **greedy online deduplication** — O(n²) in the worst case but practically fast because the selected set grows slowly. The 0.85 threshold means two tickets must be >85% semantically similar to be considered duplicates.

**Result: 197 diverse samples** selected from the IBFT ticket pool.

### Output

The selected indices are used to subset `df_ibft`:
```python
df_ibft.iloc[selected_index]
```

No explicit save in the shown cells, but this subset would be used for annotation or evaluation.

---

## Summary Comparison

| Aspect | `main.ipynb` | `discovery_data 1.ipynb` |
|--------|-------------|--------------------------|
| Purpose | Audit AI resolution quality | Sample diverse tickets for labeling |
| Data | AI system output + Freshdesk API | Labeled ticket CSV |
| Domain | Promotions + General | IBFT / ATM transfers |
| ML technique | None (pure data wrangling) | Sentence embeddings + cosine similarity dedup |
| Output | Excel reports for review | 197 representative ticket indices |
| Key issue | API key hardcoded, no error handling | Wrong embedding model (random vectors) |

---

## Bugs to Fix

### `main.ipynb`

```python
# Cell: Freshdesk API loop — add error handling
for i in ticket_id:
    url = f"https://{domain}.freshdesk.com/api/v2/tickets/{i}?include=conversations"
    response = requests.get(url, auth=HTTPBasicAuth(api_key, "X"), ...)
    time.sleep(1)
    
    if response.status_code != 200:
        print(f"Skipping {i}: HTTP {response.status_code}")
        continue
    
    response_list[i] = map_ticket_to_payload(response.json())
```

```python
# Cell: extract_problem — fix undefined variable
def extract_problem(text: str) -> str:
    description_json = parse_description_text(text)  # was: des
    full_text = ""
    selected_keys = ["Mục đích chuyển tiền", "Có liên hệ người nhận chưa", "Mô tả"]
    for key, value in description_json.items():  # was: des.items()
        if key in selected_keys:
            full_text += f"\n{key}: {value}"
    return full_text.strip()
```

### `discovery_data 1.ipynb`

```python
# Replace non-embedding model with an actual sentence embedding model
model = SentenceTransformer("keepitreal/vietnamese-sbert")
# or for multilingual coverage:
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
```

---

## Related Notes

- [[Concepts/Tokenization & Text Preprocessing]] — the `remove_transaction_info` and `parse_description_text` functions are practical examples of preprocessing
- [[Concepts/Embeddings]] — the deduplication in `discovery_data 1.ipynb` is a direct application of sentence embeddings + cosine similarity
- [[Projects/Architecture]] — both notebooks sit in the evaluation/monitoring layer of the pipeline
