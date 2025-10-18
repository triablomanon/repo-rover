# 🚀 START HERE - Repo Rover Hackathon Project

Welcome to **Repo Rover**! This guide will get you from zero to running in 15 minutes.

---

## 📋 What You Need

### Required (Must Have)
1. **Python 3.9+** installed
2. **Git** installed
3. **Internet connection** (for API calls)
4. **15 minutes** of your time

### API Keys (Get These Now)
You'll need 2 free API keys (takes ~10 minutes total):

1. ✅ **Google Gemini API** (2 min) - https://aistudio.google.com/app/apikey
2. ✅ **Vectara Account** (5 min) - https://console.vectara.com/
3. ⚠️ **Fetch.ai** (3 min, OPTIONAL) - https://agentverse.ai/

**Total cost: $0** - Everything is free tier!

---

## ⚡ Super Quick Start (5 Commands)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env and add your API keys
# (Use notepad .env on Windows, or nano .env on Mac/Linux)

# 4. Test setup
python tests/test_pipeline.py

# 5. Run demo!
python src/main.py --paper "Attention Is All You Need" --interactive
```

---

## 📖 Detailed Setup (Step-by-Step)

### Step 1: Get API Keys (10 minutes)

#### 🔑 Gemini API Key (2 minutes)
1. Visit: https://aistudio.google.com/app/apikey
2. Sign in with Google
3. Click "Create API Key"
4. Copy the key (looks like `AIzaSy...`)
5. Save it somewhere - you'll need it in Step 3!

#### 🔑 Vectara Credentials (5 minutes)
1. Visit: https://console.vectara.com/
2. Create account (free)
3. Click "Create Corpus"
   - Name: `RepoRover`
   - Click Create
4. Get **three values** and save them:
   - **Customer ID**: Account Settings → Customer ID (a number)
   - **Corpus ID**: Your corpus list → the ID number
   - **API Key**: API Access → Create API Key → Copy it (starts with `zwt_`)

**Detailed guide:** See [API_SETUP_CHECKLIST.md](API_SETUP_CHECKLIST.md)

---

### Step 2: Install Dependencies (2 minutes)

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

---

### Step 3: Configure API Keys (1 minute)

```bash
# Copy template
cp .env.example .env

# Edit the file
# Windows:
notepad .env
# Mac:
open -e .env
# Linux:
nano .env
```

Add your keys:
```env
GEMINI_API_KEY=AIzaSy...your_key_here
VECTARA_CUSTOMER_ID=1234567890
VECTARA_API_KEY=zwt_...your_key_here
VECTARA_CORPUS_ID=1
```

Save and close the file.

---

### Step 4: Test Everything (1 minute)

```bash
# Run test suite
python tests/test_pipeline.py
```

You should see:
```
=== Testing Configuration ===
✅ All required API keys configured

=== Testing Paper Finder ===
✅ Paper search working

=== Testing Vectara Connection ===
✅ Vectara connection working

=== Testing Gemini Connection ===
✅ Gemini connection working

🎉 All tests passed! Repo Rover is ready to use.
```

If you see errors, check [API_SETUP_CHECKLIST.md](API_SETUP_CHECKLIST.md)

---

### Step 5: Run Your First Demo (1 minute)

```bash
python src/main.py --paper "Attention Is All You Need" --interactive
```

This will:
1. Find the "Attention Is All You Need" paper
2. Download it from ArXiv
3. Find the GitHub repository
4. Clone and index the code
5. Create a concept map
6. Let you ask questions!

**Try these questions:**
- `Show me the multi-head attention implementation`
- `Explain positional encoding`
- `How is the transformer model structured?`

Type `exit` to quit.

---

## 🎯 What Can You Do?

### Option 1: Interactive Mode (Recommended)
```bash
python src/main.py --paper "YOUR PAPER TITLE" --interactive
```

Then ask questions naturally!

### Option 2: Single Question
```bash
python src/main.py --paper "YOUR PAPER" --question "YOUR QUESTION"
```

### Option 3: Generate Minimal Working Example
```bash
python src/main.py --paper "YOUR PAPER" --mwe "FunctionName"
```

### Option 4: Run as Agent
```bash
python src/agent.py
```

---

## 📚 Recommended Papers to Try

These are known to work well:

1. **"Attention Is All You Need"** - The Transformer
2. **"BERT"** - Bidirectional transformers
3. **"Deep Residual Learning"** - ResNet
4. **"CLIP"** - Vision-language model

---

## 🎓 Example Session

```bash
$ python src/main.py --paper "Attention Is All You Need" --interactive

Analyzing: Attention Is All You Need

Step 1: Finding Paper
✓ Found: Attention Is All You Need
  ArXiv ID: 1706.03762

Step 2: Finding Repository
✓ Found repository: https://github.com/tensorflow/tensor2tensor

Step 3: Cloning Repository
✓ Cloned to: ./cloned_repos/tensor2tensor

Step 4: Analyzing Repository
  Found 247 Python files

Step 5: Indexing Code (Vectara RAG)
✓ Indexed 189/247 files

Step 6: Initializing Query Pipeline
✓ Created concept map with 4 concepts

✓ Successfully analyzed paper and repository!

Interactive Mode
Suggested questions:
  1. Show me the Multi-Head Attention implementation
  2. Explain how positional encoding works
  3. What is the main model architecture?

Your question: Show me the multi-head attention implementation

Answer:
The multi-head attention is implemented in the MultiHeadAttention class...
[detailed explanation with code]

Your question: exit
Goodbye!
```

---

## 🐛 Troubleshooting

### "Configuration errors: GEMINI_API_KEY is required"
→ Make sure you created the `.env` file and added your API keys

### "Vectara authentication failed"
→ Double-check your Customer ID, API Key, and Corpus ID in `.env`

### "No repository found for this paper"
→ Try one of the recommended papers listed above

### Still having issues?
→ See [QUICK_START.md](QUICK_START.md) or [API_SETUP_CHECKLIST.md](API_SETUP_CHECKLIST.md)

---

## 📁 Project Files Guide

**Start here:**
- `START_HERE.md` ← You are here!
- [QUICK_START.md](QUICK_START.md) - Quick reference
- [API_SETUP_CHECKLIST.md](API_SETUP_CHECKLIST.md) - Detailed API setup

**For development:**
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - 12-hour build plan
- [README.md](README.md) - Full documentation
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - High-level overview

**For demo:**
- [notebooks/demo.ipynb](notebooks/demo.ipynb) - Google Colab notebook

---

## ⏱️ Time Breakdown

| Step | Time | What You're Doing |
|------|------|-------------------|
| Get API keys | 10 min | Sign up for Gemini & Vectara |
| Install | 2 min | `pip install -r requirements.txt` |
| Configure | 1 min | Copy API keys to `.env` |
| Test | 1 min | `python tests/test_pipeline.py` |
| First demo | 1 min | Analyze a paper! |
| **TOTAL** | **15 min** | **From zero to running** |

---

## 🎬 Demo for Hackathon Judges

Want to show this off? Here's a 3-minute demo script:

```bash
# 1. Show the problem (30 sec)
# "Researchers waste hours finding paper implementations"

# 2. Run the demo (90 sec)
python src/main.py --paper "Attention Is All You Need" --interactive

# Ask 2-3 questions live
# Generate an MWE

# 3. Show the tech (30 sec)
# "Powered by Gemini 2.0 Flash, Vectara RAG, Fetch.ai"

# 4. Q&A (30 sec)
```

---

## 🚀 Next Steps

Once you're running:

1. ✅ Try different papers
2. ✅ Ask complex questions
3. ✅ Generate MWEs
4. ✅ Deploy the agent (optional)
5. ✅ Customize for your needs

---

## 🤝 Need Help?

1. **Quick issues:** See [QUICK_START.md](QUICK_START.md)
2. **API setup:** See [API_SETUP_CHECKLIST.md](API_SETUP_CHECKLIST.md)
3. **Implementation:** See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
4. **Everything else:** See [README.md](README.md)

---

## 🎉 You're Ready!

Run this now to get started:

```bash
python src/main.py --paper "Attention Is All You Need" --interactive
```

**From paper title to running code in 60 seconds!** 🚀

---

*Built for hackathons | Powered by AI | Free forever | MIT License*
