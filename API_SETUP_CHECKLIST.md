# API Setup Checklist

Use this checklist to set up all required API keys before starting development.

## ✅ Pre-Development Checklist

### 1. Google Gemini API Key
- [ ] Go to https://aistudio.google.com/app/apikey
- [ ] Sign in with Google account
- [ ] Click "Create API Key"
- [ ] Copy API key (starts with `AIza...`)
- [ ] Add to `.env` file: `GEMINI_API_KEY=AIza...`
- [ ] Test: Run `python tests/test_pipeline.py`

**What you'll use it for:** Code synthesis, concept mapping, Q&A, MWE generation
**Free tier:** 1500 requests/day, 2M token context
**Cost:** FREE

---

### 2. Vectara RAG Platform

#### Step 2a: Create Account
- [ ] Go to https://console.vectara.com/
- [ ] Click "Sign Up"
- [ ] Verify email

#### Step 2b: Create Corpus
- [ ] Click "Create Corpus" (or "Data" → "Create Corpus")
- [ ] Fill in:
  - Name: `RepoRover-CodeSearch`
  - Description: `Semantic code search for research papers`
- [ ] Click "Create"
- [ ] **Copy the Corpus ID** (number shown in the corpus list)

#### Step 2c: Get Customer ID
- [ ] Click on your profile (top right)
- [ ] Go to "Account" or "Settings"
- [ ] Find "Customer ID" (a number like `1234567890`)
- [ ] **Copy the Customer ID**

#### Step 2d: Create API Key
- [ ] Go to "API Access" or "Authorization"
- [ ] Click "Create API Key"
- [ ] Select type: **Personal API Key** (or API Key with read/write permissions)
- [ ] Give it a name: `RepoRover`
- [ ] Click "Create"
- [ ] **Copy the API Key** (starts with `zwt_...`)
- [ ] ⚠️ Save it immediately - you won't see it again!

#### Step 2e: Add to .env
- [ ] Add to `.env` file:
  ```
  VECTARA_CUSTOMER_ID=1234567890
  VECTARA_API_KEY=zwt_...
  VECTARA_CORPUS_ID=1
  ```

**What you'll use it for:** Semantic code search, finding relevant implementations
**Free tier:** 50,000 queries/month
**Cost:** FREE

---

### 3. Fetch.ai Agentverse (Optional)

#### Step 3a: Create Account
- [ ] Go to https://agentverse.ai/
- [ ] Click "Sign Up"
- [ ] Verify email

#### Step 3b: Create Agent
- [ ] Click "Create Agent" or "New Agent"
- [ ] Choose "Blank Agent" template
- [ ] Name it: `RepoRover`

#### Step 3c: Get Credentials
- [ ] Click on your agent
- [ ] Find "Agent Address" - this is your agent's identity
- [ ] Get **Seed Phrase** (or Agent Secret Key)
- [ ] Get **Mailbox Key** (for remote communication)

#### Step 3d: Add to .env (Optional)
- [ ] Add to `.env` file:
  ```
  FETCHAI_AGENT_SEED=your_seed_phrase_here
  FETCHAI_AGENT_MAILBOX_KEY=your_mailbox_key_here
  ```

**What you'll use it for:** Agent deployment, discoverability on Agentverse
**Free tier:** Unlimited on testnet
**Cost:** FREE
**Note:** Optional for local development - only needed for Agentverse deployment

---

## Verify Setup

After completing all steps:

```bash
# 1. Check .env file exists
cat .env  # or: type .env on Windows

# 2. Run test suite
python tests/test_pipeline.py

# 3. Test configuration
python src/main.py --test
```

Expected output:
```
✅ All API keys configured
✅ Gemini Model: gemini-2.0-flash-exp
✅ Clone Directory: ./cloned_repos
✅ Ready to analyze papers!
```

---

## Your .env File Should Look Like This

```env
# Google Gemini
GEMINI_API_KEY=AIzaSyD...your_actual_key_here

# Vectara
VECTARA_CUSTOMER_ID=1234567890
VECTARA_API_KEY=zwt_AbCd...your_actual_key_here
VECTARA_CORPUS_ID=1

# Fetch.ai (Optional)
FETCHAI_AGENT_SEED=your_seed_phrase_if_deploying
FETCHAI_AGENT_MAILBOX_KEY=your_mailbox_key_if_deploying

# Optional Settings
GEMINI_MODEL=gemini-2.0-flash-exp
DEBUG=false
REPO_CLONE_DIR=./cloned_repos
```

---

## Troubleshooting

### "GEMINI_API_KEY is required"
1. Check `.env` file exists in project root
2. Check key is correct (starts with `AIza`)
3. No quotes needed around the key
4. No spaces around the `=` sign

### "Vectara authentication failed"
1. Verify Customer ID is just the number (no quotes)
2. Check API Key starts with `zwt_`
3. Verify Corpus ID matches the corpus you created
4. Make sure API key has read/write permissions

### "Gemini quota exceeded"
1. Wait for daily reset (1500 requests/day)
2. Check quota at https://aistudio.google.com/
3. Consider using a different Google account

### "Vectara corpus not found"
1. Verify Corpus ID is correct
2. Make sure corpus is in the same account
3. Check corpus hasn't been deleted

---

## API Rate Limits Summary

| Service | Free Tier | Typical Usage | Enough for Hackathon? |
|---------|-----------|---------------|----------------------|
| Gemini | 1500 req/day | 10-50 per demo | ✅ Yes, plenty |
| Vectara | 50K queries/month | 100-500 per demo | ✅ Yes, plenty |
| Fetch.ai | Unlimited (testnet) | N/A | ✅ Yes |
| ArXiv | Unlimited | 1 per paper | ✅ Yes |
| Papers with Code | Unlimited | 1 per paper | ✅ Yes |

**Total cost for hackathon: $0** 🎉

---

## Next Steps

Once all checkboxes are complete:

1. ✅ Run test suite: `python tests/test_pipeline.py`
2. ✅ Try first analysis: `python src/main.py --paper "Attention Is All You Need"`
3. ✅ Start implementing your hackathon project!

---

## Support Links

- **Gemini Docs:** https://ai.google.dev/docs
- **Vectara Docs:** https://docs.vectara.com/
- **Fetch.ai Docs:** https://docs.fetch.ai/
- **Repo Rover Issues:** See README.md

---

**Estimated Setup Time: 10-15 minutes**

Good luck with your hackathon! 🚀
