# Repo Rover

**From paper title to running code in 60 seconds**

AI agent that finds research papers, discovers code implementations, and explains how theory maps to code.

---

## Quick Setup

```bash
# 1. Create conda environment
conda env create -f environment.yml

# 2. Activate
conda activate repo-rover

# 3. Configure API keys
cp .env.example .env
# Edit .env with your Vectara and Gemini API keys

# 4. Test
python test.py
```

### Get API Keys (FREE)

1. **Vectara**: https://console.vectara.com/ → Get Customer ID + API Key
2. **Gemini**: https://aistudio.google.com/app/apikey → Get API Key

Add to `.env`:
```
VECTARA_CUSTOMER_ID=your_id
VECTARA_API_KEY=your_key
GEMINI_API_KEY=your_key
```

---

## How It Works

### `corpus_manager.py` - START HERE
Manages Vectara corpora. One corpus per paper.

```python
from src.corpus_manager import find_or_create_corpus

# Check if corpus exists for this paper, create if not
corpus_id = find_or_create_corpus("2310.02170")
# Returns: corpus_id (int) to use for indexing
```

**What it does:**
1. Lists your existing Vectara corpora
2. If corpus with paper name exists → returns its ID
3. If not → creates new corpus → returns new ID

**File interactions:**
- Reads: `.env` (for VECTARA_CUSTOMER_ID, VECTARA_API_KEY)
- Uses: Vectara API
- Returns: corpus_id for use in `code_indexer.py`

---

### Complete Workflow

```python
# 1. Get/create corpus
from src.corpus_manager import find_or_create_corpus
corpus_id = find_or_create_corpus("2310.02170")

# 2. Find paper on ArXiv
from src.discovery.paper_finder import PaperFinder
finder = PaperFinder()
paper = finder.analyze_paper("2310.02170")

# 3. Find GitHub repo
from src.discovery.repo_finder import RepoFinder
repo_finder = RepoFinder()
repo_url = repo_finder.find_with_fallback(paper)

# 4. Clone repo
from src.utils.repo_utils import RepoAnalyzer
from src.utils.config import Config
analyzer = RepoAnalyzer(Config.REPO_CLONE_DIR)
repo_path = analyzer.clone_repository(repo_url)

# 5. Index code into corpus
from src.understanding.code_indexer import VectaraIndexer
from src.utils.config import Config
indexer = VectaraIndexer(
    Config.VECTARA_CUSTOMER_ID,
    Config.VECTARA_API_KEY,
    corpus_id  # From step 1!
)
count = indexer.index_repository(repo_path, "transformer")

# 6. Query the code
results = indexer.search("multi-head attention")
```

---

## File Reference

### `src/corpus_manager.py` ⭐ NEW
**Purpose:** Manages Vectara corpora per paper

**Functions:**
- `find_or_create_corpus(name)` → corpus_id
- `delete_corpus(corpus_id)` → bool

**Depends on:** `.env` (VECTARA_CUSTOMER_ID, VECTARA_API_KEY)

**Test it:**
```bash
python src/corpus_manager.py
```

---

### `src/discovery/paper_finder.py`
**Purpose:** Finds papers on ArXiv

**Key function:** `analyze_paper(query)` → paper_info dict

**Returns:**
```python
{
    "title": "2310.02170",
    "arxiv_id": "1706.03762",
    "authors": ["Ashish Vaswani", ...],
    "summary": "...",
    "pdf_url": "...",
    "pdf_path": "/path/to/downloaded.pdf"
}
```

**Depends on:** ArXiv API (no key needed)

---

### `src/discovery/repo_finder.py`
**Purpose:** Finds GitHub repos for papers

**Key function:** `find_with_fallback(paper_info)` → repo_url

**Depends on:** Papers with Code API (no key needed)

---

### `src/understanding/code_indexer.py`
**Purpose:** Indexes code files into Vectara

**Key functions:**
- `index_repository(repo_path, name)` → count
- `search(query)` → list of results

**Depends on:**
- `.env` (VECTARA_CUSTOMER_ID, VECTARA_API_KEY)
- **corpus_id** from `corpus_manager.py`

---

### `src/understanding/gemini_synthesizer.py`
**Purpose:** Uses Gemini to explain code

**Key functions:**
- `create_concept_map(paper, readme, structure)` → dict
- `answer_question(question, code, paper)` → string
- `generate_minimal_example(function, code)` → python code

**Depends on:** `.env` (GEMINI_API_KEY)

---

### `src/understanding/query_pipeline.py`
**Purpose:** Combines Vectara search + Gemini synthesis

**Key function:** `query(question)` → answer + code snippets

**Depends on:** `code_indexer.py` + `gemini_synthesizer.py`

---

### `src/utils/config.py`
**Purpose:** Loads `.env` file

**Usage:**
```python
from src.utils.config import Config
print(Config.VECTARA_API_KEY)
```

---

### `src/utils/repo_utils.py`
**Purpose:** Git operations

**Key functions:**
- `clone_repository(url)` → repo_path
- `get_repo_structure(path)` → dict
- `get_python_files(path)` → list

---

## Project Structure

```
repo-rover/
├── src/
│   ├── corpus_manager.py      ⭐ Start here - manages Vectara corpora
│   ├── discovery/
│   │   ├── paper_finder.py    → Finds papers
│   │   └── repo_finder.py     → Finds repos
│   ├── understanding/
│   │   ├── code_indexer.py    → Indexes code (needs corpus_id)
│   │   ├── gemini_synthesizer.py  → Explains code
│   │   └── query_pipeline.py  → Combines everything
│   └── utils/
│       ├── config.py          → Loads .env
│       └── repo_utils.py      → Git helpers
├── .env                       → Your API keys
└── requirements.txt
```

---

## Data Flow

```
1. corpus_manager.py
   ↓ (returns corpus_id)

2. paper_finder.py
   ↓ (returns paper_info)

3. repo_finder.py
   ↓ (returns repo_url)

4. repo_utils.py (clone)
   ↓ (returns repo_path)

5. code_indexer.py (needs corpus_id from step 1!)
   ↓ (indexes files)

6. query_pipeline.py
   ↓ (searches + synthesizes)

7. Answer!
```

---

## Test Each Part

```bash
# 1. Test corpus manager
python src/corpus_manager.py

# 2. Test paper finding
python -c "from src.discovery.paper_finder import PaperFinder; p = PaperFinder(); print(p.search_paper('2310.02170'))"

# 3. Test repo finding
python -c "from src.discovery.repo_finder import RepoFinder; r = RepoFinder(); print(r.find_by_arxiv_id('1706.03762'))"
```

---

## Cost

All FREE:
- Vectara: 50K queries/month
- Gemini: 1500 requests/day
- ArXiv: Unlimited
- Papers with Code: Unlimited

---

## License

MIT
