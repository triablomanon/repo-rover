# Repo Rover - Implementation Plan

## Overview
This document provides a detailed 12-hour implementation plan for building Repo Rover from scratch.

## Prerequisites (Do This First!)

### Required API Keys

#### 1. Google Gemini API Key
**Time: 2 minutes**
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy key (starts with `AIza...`)
5. Add to `.env` as `GEMINI_API_KEY`

**Cost:** FREE (1500 requests/day for Gemini 2.0 Flash)

#### 2. Vectara Credentials
**Time: 5 minutes**
1. Go to https://console.vectara.com/
2. Create free account
3. Click "Create Corpus"
   - Name: "RepoRover-CodeSearch"
   - Description: "Semantic code search"
4. Note your:
   - Customer ID (in Account settings)
   - Corpus ID (in corpus list)
5. Create API Key:
   - Go to "API Access" → "Create API Key"
   - Type: Personal API Key
   - Copy the key (starts with `zwt_...`)
6. Add all three to `.env`

**Cost:** FREE (50K queries/month)

#### 3. Fetch.ai Agentverse (Optional)
**Time: 3 minutes**
1. Go to https://agentverse.ai/
2. Create free account
3. Create new agent
4. Copy agent seed phrase
5. Get mailbox key from agent settings
6. Add to `.env` (optional for local dev)

**Cost:** FREE

### Total Setup Time: ~10 minutes

---

## Phase-by-Phase Implementation

### Phase 1: Foundation (Hours 0-3)

#### Hour 0-1: Project Setup
**Goal:** Get basic infrastructure running

```bash
# Create project structure
mkdir repo-rover && cd repo-rover
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install core dependencies
pip install python-dotenv requests rich

# Test imports
python -c "import dotenv, requests; print('✓ Setup works')"
```

**Files to create:**
- [x] `.env.example` - Template for API keys
- [x] `requirements.txt` - All dependencies
- [x] `.gitignore` - Ignore secrets and clones
- [x] `src/utils/config.py` - Configuration management

**Checkpoint:** Can import all modules without errors

#### Hour 1-2: Paper Discovery
**Goal:** Download papers from ArXiv

```bash
pip install arxiv PyPDF2
```

**Implementation:**
- [x] `src/discovery/paper_finder.py`
  - `search_paper(query)` - Search ArXiv
  - `download_paper(paper_info)` - Get PDF
  - `analyze_paper(query)` - Complete pipeline

**Test:**
```python
from discovery.paper_finder import PaperFinder
finder = PaperFinder()
paper = finder.analyze_paper("Attention Is All You Need")
print(paper['title'])  # Should print paper title
```

**Checkpoint:** Can download "Attention Is All You Need" PDF

#### Hour 2-3: Repository Discovery
**Goal:** Find GitHub repos for papers

```bash
pip install beautifulsoup4
```

**Implementation:**
- [x] `src/discovery/repo_finder.py`
  - `find_by_arxiv_id()` - Use Papers with Code API
  - `find_by_title()` - Search by paper title
  - `get_known_repos()` - Hardcoded fallback

**Test:**
```python
from discovery.repo_finder import RepoFinder
finder = RepoFinder()
repo = finder.find_by_arxiv_id("1706.03762")
print(repo)  # Should print tensor2tensor URL
```

**Checkpoint:** Returns repository URL for Transformer paper

---

### Phase 2: Code Understanding (Hours 3-8)

#### Hour 3-4: Vectara Integration
**Goal:** Index code for semantic search

**Implementation:**
- [x] `src/understanding/code_indexer.py`
  - `index_file()` - Index single file
  - `index_repository()` - Index all Python files
  - `search()` - Query indexed code

**Test:**
```python
from understanding.code_indexer import VectaraIndexer
indexer = VectaraIndexer(CUSTOMER_ID, API_KEY, CORPUS_ID)

# Clone a repo first
from utils.repo_utils import RepoAnalyzer
analyzer = RepoAnalyzer("./cloned_repos")
repo_path = analyzer.clone_repository("https://github.com/tensorflow/tensor2tensor")

# Index it
count = indexer.index_repository(repo_path, "transformer")
print(f"Indexed {count} files")

# Search
results = indexer.search("attention mechanism")
print(results)
```

**Common Issues:**
- **401 Unauthorized:** Check API key and customer ID
- **Corpus not found:** Verify corpus ID
- **Rate limit:** Free tier is 50K/month, should be fine

**Checkpoint:** Can search indexed code and get results

#### Hour 4-6: Gemini Synthesis
**Goal:** Generate concept maps and explanations

```bash
pip install google-generativeai
```

**Implementation:**
- [x] `src/understanding/gemini_synthesizer.py`
  - `create_concept_map()` - Map paper concepts to code
  - `explain_code_concept()` - Explain implementations
  - `answer_question()` - Q&A
  - `generate_minimal_example()` - Create MWEs

**Test:**
```python
from understanding.gemini_synthesizer import GeminiSynthesizer
gemini = GeminiSynthesizer(GEMINI_API_KEY)

# Create concept map
concept_map = gemini.create_concept_map(
    paper_info,
    readme_content,
    repo_structure
)
print(concept_map['main_concepts'])
```

**Common Issues:**
- **Quota exceeded:** Wait for daily reset (1500 requests/day)
- **JSON parse error:** Fallback map is used automatically
- **Context too large:** Pre-chunk to < 1M tokens

**Checkpoint:** Can map "Multi-Head Attention" to correct file

#### Hour 6-7: Query Pipeline
**Goal:** Combine Vectara + Gemini

**Implementation:**
- [x] `src/understanding/query_pipeline.py`
  - `initialize()` - Set up with repo context
  - `query()` - Answer questions
  - `explain_concept()` - Detailed explanations
  - `generate_mwe()` - Create examples

**Test:**
```python
from understanding.query_pipeline import QueryPipeline
pipeline = QueryPipeline(vectara, gemini, paper_info, repo_path)
pipeline.initialize(readme, repo_structure)

response = pipeline.query("Explain multi-head attention")
print(response['answer'])
```

**Checkpoint:** Can answer 3+ questions accurately

#### Hour 7-8: Repository Utilities
**Goal:** Git operations and file handling

```bash
pip install GitPython
```

**Implementation:**
- [x] `src/utils/repo_utils.py`
  - `clone_repository()` - Shallow clone
  - `get_repo_structure()` - File tree
  - `get_python_files()` - List Python files
  - `get_readme_content()` - Read README

**Checkpoint:** Can clone and analyze repository structure

---

### Phase 3: Agent Deployment (Hours 8-10)

#### Hour 8-9: Main Application
**Goal:** Complete CLI interface

**Implementation:**
- [x] `src/main.py`
  - `RepoRover` class - Main orchestrator
  - `analyze_paper()` - Full pipeline
  - `query()` - Ask questions
  - `interactive_mode()` - Chat interface
  - `generate_mwe()` - Create examples

**Test:**
```bash
# Test configuration
python src/main.py --test

# Analyze paper
python src/main.py --paper "Attention Is All You Need"

# Ask question
python src/main.py --paper "Attention Is All You Need" --question "Show me multi-head attention"

# Interactive mode
python src/main.py --paper "Attention Is All You Need" --interactive
```

**Checkpoint:** End-to-end pipeline works locally

#### Hour 9-10: Fetch.ai Agent
**Goal:** Deploy on Agentverse

```bash
pip install uagents
```

**Implementation:**
- [x] `src/agent.py`
  - Message models (Request/Response)
  - `handle_analyze_paper()` - Paper analysis handler
  - `handle_query()` - Query handler
  - `handle_mwe()` - MWE generation handler

**Test (Local):**
```bash
python src/agent.py
```

**Deploy to Agentverse:**
1. Go to https://agentverse.ai/
2. Create new agent
3. Upload `agent.py` code
4. Configure environment variables
5. Deploy and test

**Alternative (if Agentverse issues):**
Run locally and show architecture diagram in presentation

**Checkpoint:** Agent responds to messages

---

### Phase 4: Demo Polish (Hours 10-12)

#### Hour 10-11: Colab Notebook
**Goal:** Presentation-ready demo

**Implementation:**
- [x] `notebooks/demo.ipynb`
  - Setup cells (API keys)
  - Paper analysis demo
  - Q&A examples
  - MWE generation
  - Partner tool mentions

**Test:**
1. Upload to Google Colab
2. Run all cells
3. Verify < 3 minute execution

**Checkpoint:** Complete notebook runs end-to-end

#### Hour 11-12: Presentation Prep
**Goal:** Polish for judges

**Tasks:**
1. **Documentation:**
   - [x] Detailed README with setup
   - [x] API key instructions
   - Architecture diagram (optional)

2. **Demo Script:**
   ```
   [30s] Problem: "Researchers waste hours finding implementations"
   [90s] Demo: Live notebook or pre-recorded
   [30s] Tech: "Powered by Gemini, Vectara, Fetch.ai"
   [30s] Q&A
   ```

3. **Backup Video:**
   Record successful demo run in case of live issues

4. **Talking Points:**
   - "2M token context with Gemini 2.0 Flash"
   - "Semantic search via Vectara RAG"
   - "Discoverable on Fetch.ai Agentverse"
   - "Working MWE in < 60 seconds"

**Checkpoint:** 3-minute pitch ready

---

## Critical Path Summary

### Must Work for Demo:
1. ✅ `analyze_paper("Attention Is All You Need")` → success
2. ✅ `query("Explain multi-head attention")` → answer + code
3. ✅ `generate_mwe("MultiHeadAttention")` → runnable script
4. ⚠️ Agent visible on Agentverse (or local fallback)

### Emergency Shortcuts:

**If Vectara fails (Hour 6):**
```python
# Fallback to simple grep
def fallback_search(query, repo_path):
    import subprocess
    result = subprocess.run(['grep', '-r', query, repo_path], capture_output=True)
    return result.stdout.decode()
```

**If Gemini fails (Hour 8):**
```python
# Hardcode concept map for Transformer
FALLBACK_MAP = {
    "main_concepts": [
        {"concept": "Multi-Head Attention", "likely_files": ["transformer.py"]}
    ]
}
```

**If Agentverse fails (Hour 10):**
1. Show local agent running
2. Display architecture diagram
3. Demo CLI instead

---

## Testing Checklist

Before demo, verify:
- [ ] API keys in `.env` work
- [ ] Can analyze "Attention Is All You Need"
- [ ] Can answer 3 different questions
- [ ] MWE generates and runs
- [ ] Notebook executes in < 3 minutes
- [ ] All partner tools mentioned in output

---

## Common Pitfalls

### API Rate Limits
- **Gemini:** 1500 req/day (plenty for demo)
- **Vectara:** 50K queries/month (plenty)
- **ArXiv:** No limit
- **Solution:** Cache results, avoid re-indexing

### Large Context
- **Problem:** Some repos are huge
- **Solution:** Index only Python files, skip tests
- **Fallback:** Use --depth 1 for shallow clone

### Network Issues
- **Problem:** GitHub/API timeouts
- **Solution:** Hardcode known repos as fallback
- **Demo:** Use cached results if needed

---

## Resource Summary

| Resource | Free Tier | Used For | Critical? |
|----------|-----------|----------|-----------|
| Gemini API | 1500 req/day | Synthesis | ✅ Yes |
| Vectara | 50K queries/month | Code search | ✅ Yes |
| Fetch.ai | Unlimited testnet | Deployment | ⚠️ Nice-to-have |
| ArXiv | Unlimited | Papers | ✅ Yes |
| Papers with Code | Unlimited | Repos | ✅ Yes |

**Total Cost: $0**

---

## Success Metrics

✅ Complete end-to-end demo with 1 paper
✅ Answer 3+ questions accurately
✅ Generate 1 working MWE
✅ Demo completes in < 3 minutes
✅ All partner tools integrated and mentioned

---

## Next Steps After Hackathon

1. Add multi-language support (Java, C++, Rust)
2. PDF parsing for diagrams
3. Video tutorials
4. Web interface
5. More sophisticated MWE validation

---

**Total Time: 12 hours**
**Deliverable: Live demo + deployed agent + Colab notebook**
**Success: Judges see paper → code → explanation → MWE**
