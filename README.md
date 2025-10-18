# Repo Rover

**Tagline:** From paper title to running code in 60 seconds

An autonomous AI agent that finds research papers, discovers their code implementations, and provides interactive step-by-step explanations connecting theory to code.

## Quick Start

### 1. Prerequisites

- Python 3.9 or higher
- Git installed
- API keys (see setup below)

### 2. Required API Keys Setup

Before you begin, obtain these API keys:

#### A. Google Gemini API Key (REQUIRED)
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

#### B. Vectara Credentials (REQUIRED)
1. Visit [Vectara Console](https://console.vectara.com/)
2. Create a free account
3. Create a new corpus:
   - Go to "Data" > "Create Corpus"
   - Name: "RepoRover-CodeSearch"
   - Description: "Semantic search for code repositories"
4. Get your credentials:
   - **Customer ID**: Found in Account settings
   - **API Key**: Create under "API Access" > "Create API Key" (select "Personal API Key")
   - **Corpus ID**: The ID of your created corpus (visible in corpus list)

#### C. Fetch.ai Agentverse (OPTIONAL - For deployment)
1. Visit [Agentverse](https://agentverse.ai/)
2. Create a free account
3. Create a new agent to get:
   - Agent seed phrase
   - Mailbox key (for remote communication)

### 3. Installation

```bash
# Clone the repository
cd repo-rover

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Windows: notepad .env
# Linux/Mac: nano .env
```

### 4. Configuration

Edit [.env](.env) file with your actual API keys:

```env
GEMINI_API_KEY=AIza...your_actual_key
VECTARA_CUSTOMER_ID=1234567890
VECTARA_API_KEY=zwt_...your_actual_key
VECTARA_CORPUS_ID=1
```

### 5. Run

```bash
# Test the setup
python src/main.py --test

# Analyze a paper
python src/main.py --paper "Attention Is All You Need"

# Start the agent
python src/agent.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Input                           │
│            "Analyze: Attention Is All You Need"         │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Paper Discovery Module                      │
│  ┌─────────────┐         ┌──────────────┐              │
│  │ ArXiv API   │────────▶│ PDF Download │              │
│  └─────────────┘         └──────────────┘              │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│            Repository Discovery Module                   │
│  ┌──────────────────┐       ┌──────────────┐           │
│  │ Papers w/ Code   │──────▶│ Git Clone    │           │
│  │ API              │       │ Repository   │           │
│  └──────────────────┘       └──────────────┘           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Code Understanding Engine                   │
│  ┌──────────────┐         ┌──────────────┐             │
│  │   Vectara    │────────▶│   Gemini     │             │
│  │  RAG Search  │         │  Synthesis   │             │
│  └──────────────┘         └──────────────┘             │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Fetch.ai uAgent Layer                       │
│  ┌────────────────────────────────────────┐             │
│  │  Deployed on Agentverse                │             │
│  │  - Natural Language Q&A                │             │
│  │  - MWE Generation                      │             │
│  │  - Interactive Explanations            │             │
│  └────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
repo-rover/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Main entry point
│   ├── agent.py                   # Fetch.ai agent wrapper
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── paper_finder.py        # ArXiv integration
│   │   └── repo_finder.py         # Papers with Code API
│   ├── understanding/
│   │   ├── __init__.py
│   │   ├── code_indexer.py        # Vectara RAG integration
│   │   ├── gemini_synthesizer.py  # Gemini integration
│   │   └── query_pipeline.py      # Combined query handler
│   ├── generation/
│   │   ├── __init__.py
│   │   └── mwe_generator.py       # Minimal working example
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # Configuration management
│       └── repo_utils.py          # Git utilities
├── tests/
│   └── test_pipeline.py
├── notebooks/
│   └── demo.ipynb                 # Colab demo
├── cloned_repos/                  # Git clones (gitignored)
├── .env.example
├── .gitignore
├── requirements.txt
├── environment.yml                # Conda environment
└── README.md
```

## API Key Costs (All Free Tier Available)

| Service | Free Tier | Cost After | What We Use It For |
|---------|-----------|------------|-------------------|
| **Gemini 2.0 Flash** | 1500 requests/day, 2M tokens | $0 (currently free) | Code synthesis, concept mapping |
| **Vectara** | 50K queries/month | Free for developers | Semantic code search |
| **Fetch.ai** | Unlimited testnet | Free | Agent deployment |
| **ArXiv API** | Unlimited | Free | Paper downloads |
| **Papers with Code** | Unlimited | Free | Repo discovery |

**Total Setup Cost: $0**

## Development Timeline (12 Hours)

- **Hours 0-3:** Foundation (Paper + Repo Discovery) ✓
- **Hours 3-8:** Code Understanding (Vectara + Gemini)
- **Hours 8-10:** Agent Deployment (Fetch.ai)
- **Hours 10-12:** Demo Polish (Colab + Presentation)

## Demo Flow (3 Minutes)

1. **Input:** "Analyze: Attention Is All You Need"
2. **Agent finds:** ArXiv paper + tensor2tensor repo
3. **User asks:** "Show me multi-head attention implementation"
4. **Agent returns:** Explanation + code snippet from `transformer.py`
5. **User requests:** "Generate MWE for MultiHeadAttention"
6. **Agent creates:** Runnable Python script with dummy data

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'uagents'"**
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt`

**"Vectara authentication failed"**
- Double-check Customer ID, API Key, and Corpus ID in [.env](.env)
- Ensure API key has read/write permissions

**"Gemini API quota exceeded"**
- Wait for quota reset (1500 requests/day)
- Consider using smaller code chunks

**"Papers with Code API not finding repository"**
- Some papers don't have official implementations
- Try fallback search or hardcode known paper-repo pairs

## Contributing

This is a hackathon project! Feel free to:
- Add support for more paper sources
- Improve code understanding algorithms
- Add multi-language support
- Enhance MWE generation

## License

MIT License - Built for [Hackathon Name]

## Powered By

- [Google Gemini](https://ai.google.dev/) - Long-context code understanding
- [Vectara](https://vectara.com/) - Semantic code search
- [Fetch.ai](https://fetch.ai/) - Agent deployment & discovery
- [Papers with Code](https://paperswithcode.com/) - Repository discovery

---

**Built in 12 hours | From paper title to running code in 60 seconds**
