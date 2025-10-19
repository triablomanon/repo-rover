# Build Order for Repo Rover

Build components in this order. Test each one before moving to the next.

---

## 1️⃣ Config & Environment
**File:** `src/utils/config.py`
**Status:** ✅ Already built

**What it does:** Loads API keys from `.env` file

**Test:**
```bash
python -c "from src.utils.config import Config; print(Config.GEMINI_API_KEY[:10])"
```

---

## 2️⃣ Corpus Manager
**File:** `src/corpus_manager.py`
**Status:** ✅ Already built

**What it does:** Creates/finds Vectara corpus for each paper

**Dependencies:** Config

**Test:**
```bash
python src/corpus_manager.py
```

---

## 3️⃣ Paper Finder
**File:** `src/discovery/paper_finder.py`
**Status:** ✅ Already built

**What it does:** Searches ArXiv for papers

**Dependencies:** None (uses ArXiv API)

**Test:**
```bash
python -c "from src.discovery.paper_finder import PaperFinder; p = PaperFinder(); print(p.search_paper('2310.02170'))"
```

---

## 4️⃣ Repo Finder
**File:** `src/discovery/repo_finder.py`
**Status:** ✅ Already built

**What it does:** Extracts GitHub repo URL from PDF using Gemini

**Dependencies:**
- Paper Finder (needs PDF downloaded)
- Gemini API
- Config

**How it works:**
1. Takes paper_info dict with `pdf_path` key
2. Uploads PDF to Gemini
3. Prompts Gemini to extract GitHub URL
4. Falls back to hardcoded repos if needed

**Test:**
```bash
# Tested in test.py (requires PDF from paper_finder)
python test.py
```

---

## 5️⃣ Repo Utils
**File:** `src/utils/repo_utils.py`
**Status:** ✅ Already built

**What it does:** Clones repos, analyzes structure

**Dependencies:** GitPython, Config

**Test:**
```bash
python -c "from src.utils.repo_utils import RepoAnalyzer; from src.utils.config import Config; a = RepoAnalyzer(Config.REPO_CLONE_DIR); print('Ready')"
```

---

## 6️⃣ Code Indexer
**File:** `src/understanding/code_indexer.py`
**Status:** ✅ Already built

**What it does:** Indexes Python files into Vectara corpus

**Dependencies:** Corpus Manager (for corpus_id), Config

**Test:**
```bash
# Requires corpus_id from test 02
python test.py
```

---

## 7️⃣ Gemini Synthesizer
**File:** `src/understanding/gemini_synthesizer.py`
**Status:** ✅ Already built

**What it does:** Uses Gemini to explain code, create concept maps

**Dependencies:** Config (for Gemini API key)

**Test:**
```bash
# Tested in test.py
python test.py
```

---

## 8️⃣ Query Pipeline
**File:** `src/understanding/query_pipeline.py`
**Status:** ✅ Already built

**What it does:** Combines Vectara search + Gemini synthesis

**Dependencies:** Code Indexer, Gemini Synthesizer

**Test:**
```bash
# Full integration test
python test.py
```

---

## Component Dependency Graph

```
.env file
   ↓
Config (utils/config.py)
   ↓
   ├─→ Corpus Manager ────────────────┐
   │                                   ↓
   ├─→ Paper Finder (downloads PDF)  Code Indexer
   │        ↓                           ↓
   │   Repo Finder (uses PDF+Gemini)   │
   │        ↓                           │
   ├─→ Repo Utils                      │
   │                                   │
   └─→ Gemini Synthesizer ─────────────┤
                                       ↓
                              Query Pipeline
```

**Key:** Repo Finder now uses Gemini to extract GitHub URLs from PDFs

---

## Testing Strategy

### Step 1: Test individually
```bash
# Test each component as you build it
python test.py
```

### Step 2: Full integration test
```bash
# After all components are built
python test.py
```

Expected output:
```
config................................................. ✓ PASS
corpus................................................ ✓ PASS
paper................................................. ✓ PASS
repo_url.............................................. ✓ PASS
repo_clone............................................ ✓ PASS
indexer............................................... ✓ PASS
gemini................................................ ✓ PASS
pipeline.............................................. ✓ PASS

Result: 8/8 tests passed
```

---

## Current Status

All components are **already built**! ✅

Just need to:
1. Set up `.env` with your API keys
2. Run `python test.py` to verify everything works
3. Start using the system!

---

## Next: Use the System

After all tests pass, you can use the full pipeline:

```python
from src.corpus_manager import find_or_create_corpus
from src.discovery.paper_finder import PaperFinder
from src.discovery.repo_finder import RepoFinder
from src.utils.repo_utils import RepoAnalyzer
from src.understanding.code_indexer import VectaraIndexer
from src.understanding.gemini_synthesizer import GeminiSynthesizer
from src.understanding.query_pipeline import QueryPipeline
from src.utils.config import Config

# 1. Get corpus
corpus_id = find_or_create_corpus("2310.02170")

# 2. Find paper
paper = PaperFinder().analyze_paper("2310.02170")

# 3. Find & clone repo
repo_url = RepoFinder().find_with_fallback(paper)
repo_path = RepoAnalyzer(Config.REPO_CLONE_DIR).clone_repository(repo_url)

# 4. Index code
indexer = VectaraIndexer(Config.VECTARA_CUSTOMER_ID, Config.VECTARA_API_KEY, corpus_id)
indexer.index_repository(repo_path, "transformer")

# 5. Query
gemini = GeminiSynthesizer(Config.GEMINI_API_KEY)
pipeline = QueryPipeline(indexer, gemini, paper, repo_path)
pipeline.initialize("", {})

response = pipeline.query("Explain multi-head attention")
print(response['answer'])
```
