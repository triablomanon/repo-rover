# Quick Start - Repo Rover

## Setup (3 steps)

```bash
# 1. Create environment
conda env create -f environment.yml
conda activate repo-rover

# 2. Configure API keys
cp .env.example .env
# Edit .env with your keys:
#   VECTARA_CUSTOMER_ID=...
#   VECTARA_API_KEY=...
#   GEMINI_API_KEY=...

# 3. Test everything
python test.py
```

---

## Get API Keys

**Vectara** (5 min)
1. https://console.vectara.com/
2. Sign up → Get Customer ID + API Key

**Gemini** (2 min)
1. https://aistudio.google.com/app/apikey
2. Create API Key

Both are **FREE**!

---

## What Gets Tested

`test.py` runs 8 sequential tests:

1. ✓ Config - Load API keys
2. ✓ Corpus Manager - Create Vectara corpus
3. ✓ Paper Finder - Search ArXiv
4. ✓ Repo Finder - Find GitHub repo
5. ✓ Repo Utils - Clone repository
6. ✓ Code Indexer - Index into Vectara
7. ✓ Gemini - AI synthesis
8. ✓ Pipeline - Full integration

---

## Files

- `test.py` - Test all components
- `BUILD_ORDER.md` - Development sequence
- `README.md` - Full documentation
- `environment.yml` - Conda environment

---

## Daily Use

```bash
conda activate repo-rover
python test.py
```

That's it! 🚀
