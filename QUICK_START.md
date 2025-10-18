# Repo Rover - Quick Start Guide

## TL;DR - Get Running in 5 Minutes

```bash
# 1. Install
git clone https://github.com/YOUR_USERNAME/repo-rover.git
cd repo-rover
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure (copy .env.example to .env and fill in your keys)
cp .env.example .env
# Edit .env with your API keys

# 3. Test
python src/main.py --test

# 4. Run
python src/main.py --paper "Attention Is All You Need" --interactive
```

---

## Required API Keys (Get These First!)

### 1. Google Gemini API Key (2 minutes)
**Used for:** Code synthesis, explanations, MWE generation

1. Visit: https://aistudio.google.com/app/apikey
2. Sign in → Click "Create API Key"
3. Copy key (starts with `AIza...`)
4. Add to `.env`: `GEMINI_API_KEY=AIza...`

**Free Tier:** 1500 requests/day, 2M token context

---

### 2. Vectara Credentials (5 minutes)
**Used for:** Semantic code search (RAG)

1. Visit: https://console.vectara.com/
2. Create account → Click "Create Corpus"
   - Name: `RepoRover-CodeSearch`
3. Get three values:
   - **Customer ID:** Account settings → Copy number
   - **Corpus ID:** Corpus list → Copy number
   - **API Key:** API Access → Create API Key → Copy (starts with `zwt_...`)
4. Add to `.env`:
   ```
   VECTARA_CUSTOMER_ID=1234567890
   VECTARA_API_KEY=zwt_...
   VECTARA_CORPUS_ID=1
   ```

**Free Tier:** 50K queries/month

---

### 3. Fetch.ai Agentverse (3 minutes, OPTIONAL)
**Used for:** Agent deployment (optional for local use)

1. Visit: https://agentverse.ai/
2. Create account → Create new agent
3. Copy seed phrase and mailbox key
4. Add to `.env` (optional):
   ```
   FETCHAI_AGENT_SEED=your_seed_phrase
   FETCHAI_AGENT_MAILBOX_KEY=your_key
   ```

**Free Tier:** Unlimited on testnet

---

## Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/repo-rover.git
cd repo-rover

# Create virtual environment
python -m venv venv

# Activate (choose your platform)
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration

```bash
# Copy template
cp .env.example .env

# Edit .env file (use your favorite editor)
# Windows:
notepad .env
# Linux/Mac:
nano .env
```

Add your API keys:
```env
GEMINI_API_KEY=AIza...your_key_here
VECTARA_CUSTOMER_ID=1234567890
VECTARA_API_KEY=zwt_...your_key_here
VECTARA_CORPUS_ID=1
```

---

## Test Your Setup

```bash
python src/main.py --test
```

Expected output:
```
✓ All API keys configured
✓ Gemini Model: gemini-2.0-flash-exp
✓ Clone Directory: ./cloned_repos
✓ Ready to analyze papers!
```

---

## Basic Usage

### Analyze a Paper
```bash
python src/main.py --paper "Attention Is All You Need"
```

This will:
1. ✅ Find paper on ArXiv
2. ✅ Download PDF
3. ✅ Find GitHub repository
4. ✅ Clone repository
5. ✅ Index code with Vectara
6. ✅ Create concept map with Gemini

### Ask Questions
```bash
python src/main.py --paper "Attention Is All You Need" \
  --question "Show me the multi-head attention implementation"
```

### Interactive Mode (Recommended!)
```bash
python src/main.py --paper "Attention Is All You Need" --interactive
```

Then ask questions:
```
Your question: Explain positional encoding
Your question: Show me the training loop
Your question: How is the loss function implemented?
```

### Generate Minimal Working Example
```bash
python src/main.py --paper "Attention Is All You Need" \
  --mwe "MultiHeadAttention"
```

This creates a runnable Python script demonstrating the function.

---

## Run as Fetch.ai Agent

```bash
python src/agent.py
```

The agent will:
- Listen for requests on port 8001
- Accept AnalyzePaperRequest, QueryRequest, MWERequest messages
- Respond with formatted answers

**To deploy on Agentverse:** Follow instructions in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)

---

## Demo Notebook (Google Colab)

1. Open `notebooks/demo.ipynb` in Google Colab
2. Run setup cells
3. Enter API keys when prompted
4. Follow the interactive demo

**Demo includes:**
- Paper analysis
- Question answering
- MWE generation
- Multiple paper examples

---

## Common Issues

### "Configuration errors: GEMINI_API_KEY is required"
**Solution:** Make sure you created `.env` file and added your API keys

### "Vectara authentication failed"
**Solution:** Double-check Customer ID, API Key, and Corpus ID in `.env`

### "No repository found for this paper"
**Solution:** Some papers don't have implementations. Try these known working examples:
- "Attention Is All You Need"
- "BERT: Pre-training of Deep Bidirectional Transformers"
- "Deep Residual Learning for Image Recognition"

### "Failed to clone repository"
**Solution:** Check internet connection and ensure Git is installed

---

## Example Session

```bash
$ python src/main.py --paper "Attention Is All You Need" --interactive

Analyzing: Attention Is All You Need

Step 1: Finding Paper
✓ Found: Attention Is All You Need

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
Ask questions about the paper and code. Type 'exit' to quit.

Suggested questions:
  1. Show me the Multi-Head Attention implementation
  2. Explain how positional encoding works
  3. What is the main model architecture?

Your question: Show me the Multi-Head Attention implementation

Answer:
The multi-head attention mechanism is implemented in the `MultiHeadAttention`
class in `tensor2tensor/layers/common_attention.py`. The implementation splits
the input into multiple heads, applies scaled dot-product attention to each
head independently, and then concatenates the results...

[Detailed answer with code snippets]

Your question: exit

Goodbye!
```

---

## What's Next?

1. **Try different papers** - BERT, ResNet, Vision Transformer
2. **Generate MWEs** - Create standalone examples
3. **Deploy agent** - Put on Agentverse for discovery
4. **Customize** - Add your own concept mappings

---

## Resources

- **Documentation:** [README.md](README.md)
- **Implementation Plan:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- **Demo Notebook:** [notebooks/demo.ipynb](notebooks/demo.ipynb)

---

## Getting Help

### API Documentation
- Gemini: https://ai.google.dev/docs
- Vectara: https://docs.vectara.com/
- Fetch.ai: https://docs.fetch.ai/

### Issues
If you encounter problems:
1. Check [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for troubleshooting
2. Verify API keys are correct
3. Ensure all dependencies are installed
4. Try with a known working paper first

---

**Total setup time: ~10 minutes**

**From paper title to running code in 60 seconds!** 🚀
