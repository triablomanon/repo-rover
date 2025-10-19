# Railway Deployment + Hybrid Fetch.ai Architecture Guide

## Overview

This guide explains how to:
1. Deploy both your Flask API and uAgents agent to Railway
2. Create a hosted agent on Fetch.ai that routes requests to your Railway agent
3. Make Repo Rover accessible through DeltaV/ASI:One

## Architecture

```
┌─────────────────┐
│   DeltaV User   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Hosted Agent           │  (Runs on Fetch.ai cloud)
│  - Receives ChatMessage │  - Simple router/proxy
│  - Parses intent        │  - ~100 lines of code
│  - Routes to Railway    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Railway Agent          │  (Your full agent.py)
│  - SearchPaperRequest   │  - Heavy processing
│  - InitPaperRequest     │  - File system access
│  - ChatRequest          │  - ChromaDB, Git, etc.
└─────────────────────────┘
```

---

## Part 1: Railway Deployment

### Files Updated

✅ **start.sh** - Fixed to run both servers:
```bash
# Runs agent.py in background (for AgentVerse)
python backend/src/agent.py &

# Runs api_server.py in foreground (for web frontend)
gunicorn backend.api_server:app
```

✅ **requirements.txt** - Added gunicorn

✅ **agent.py** - Dynamic endpoint using Railway domain:
```python
railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
agent_endpoint = f"https://{railway_domain}/submit" if railway_domain else "http://localhost:8001/submit"
```

### Railway Configuration

1. **Environment Variables to Set:**
   ```
   RAILWAY_PUBLIC_DOMAIN=your-app.railway.app
   GEMINI_API_KEY=<your_key>
   FETCHAI_AGENT_SEED=arxini_research_code_companion_seed
   CHROMA_PATH=./chroma_db
   REPO_CLONE_DIR=./cloned_repos
   ```

2. **Port:** Railway automatically sets `$PORT` - no config needed

3. **Deploy:**
   ```bash
   git add .
   git commit -m "Configure Railway deployment"
   git push
   ```

### Testing Railway Deployment

1. **Test Flask API (Web Frontend):**
   ```
   GET https://your-app.railway.app/health
   ```

2. **Test uAgents Agent:**
   - Agent will register with AgentVerse automatically via mailbox
   - Check logs for: `Agent address: agent1q...`
   - Copy this address for the hosted agent

---

## Part 2: Hosted Agent Router (Fetch.ai Cloud)

### What It Does

The hosted agent is a **lightweight proxy** that:
1. Receives natural language from DeltaV users
2. Parses the intent (search paper? ask question?)
3. Forwards appropriate message to Railway agent
4. Returns response to user

### Implementation

**Create in Agentverse Web UI:**

Go to Agentverse → Create Hosted Agent → Paste this code:

```python
from datetime import datetime
from uuid import uuid4
from uagents import Context, Protocol, Agent
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

# ============================================================================
# CONFIGURATION - UPDATE THESE!
# ============================================================================

# Your Railway agent address (from Railway deployment logs)
RAILWAY_AGENT_ADDRESS = "agent1q..."  # Copy from Railway logs

# ============================================================================
# HOSTED AGENT SETUP
# ============================================================================

agent = Agent()
protocol = Protocol(spec=chat_protocol_spec)

# ============================================================================
# INTENT PARSING
# ============================================================================

def parse_intent(text: str):
    """
    Simple intent parser - determines what the user wants to do
    Returns: (intent_type, parsed_data)
    """
    text_lower = text.lower()

    # Search for papers
    if any(word in text_lower for word in ["search", "find", "look for", "papers about"]):
        # Extract search query
        query = text.replace("search for", "").replace("find", "").replace("papers about", "").strip()
        return ("search_paper", {"query": query, "use_gemini": True, "max_results": 3})

    # Initialize/load a paper
    elif any(word in text_lower for word in ["load", "open", "initialize", "init"]):
        # Extract arxiv ID (pattern: YYMM.NNNNN)
        import re
        arxiv_match = re.search(r'\d{4}\.\d{4,5}', text)
        if arxiv_match:
            return ("init_paper", {"arxiv_id": arxiv_match.group(0)})

    # Ask question about paper
    else:
        return ("chat", {"message": text})

    return (None, None)


# ============================================================================
# MESSAGE HANDLERS
# ============================================================================

@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Main handler - receives from DeltaV, routes to Railway"""

    # Send acknowledgement
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )

    # Extract text from message
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text

    ctx.logger.info(f"Received: {text}")

    # Parse intent
    intent_type, data = parse_intent(text)

    if not intent_type:
        response = "I couldn't understand your request. You can:\n- Search for papers\n- Initialize a paper (provide arxiv ID)\n- Ask questions about a loaded paper"
    else:
        # Forward to Railway agent
        ctx.logger.info(f"Intent: {intent_type}, Data: {data}")

        try:
            if intent_type == "search_paper":
                # Create SearchPaperRequest message
                from uagents import Model

                class SearchPaperRequest(Model):
                    query: str
                    use_gemini: bool = True
                    max_results: int = 3

                await ctx.send(
                    RAILWAY_AGENT_ADDRESS,
                    SearchPaperRequest(**data)
                )
                response = f"Searching for papers about '{data['query']}'... Please wait."

            elif intent_type == "init_paper":
                class InitPaperRequest(Model):
                    session_id: str
                    arxiv_id: str

                # Generate session ID
                session_id = str(uuid4())
                await ctx.send(
                    RAILWAY_AGENT_ADDRESS,
                    InitPaperRequest(session_id=session_id, arxiv_id=data["arxiv_id"])
                )
                response = f"Loading paper {data['arxiv_id']}... This may take 30-60 seconds."

            elif intent_type == "chat":
                class ChatRequest(Model):
                    session_id: str
                    message: str

                # Use stored session ID (you'll need to manage this)
                session_id = str(uuid4())  # Simplified for now
                await ctx.send(
                    RAILWAY_AGENT_ADDRESS,
                    ChatRequest(session_id=session_id, message=data["message"])
                )
                response = "Processing your question..."

        except Exception as e:
            ctx.logger.error(f"Error forwarding to Railway: {e}")
            response = f"Sorry, I couldn't connect to the backend. Error: {str(e)}"

    # Send response back to DeltaV user
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text=response),
            EndSessionContent(type="end-session"),
        ]
    ))


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle acknowledgements from Railway agent"""
    pass


# TODO: Add handlers for SearchPaperResponse, InitPaperResponse, ChatResponse
# These will receive responses from Railway agent and forward back to DeltaV user

# ============================================================================
# AGENT INITIALIZATION
# ============================================================================

agent.include(protocol, publish_manifest=True)
```

### README Configuration

**Important:** Fill out the README in Agentverse to help ASI:One discover your agent:

```markdown
# Repo Rover - Research Paper Code Companion

I help researchers understand academic papers by analyzing their code implementations.

## What I Can Do

1. **Search for Papers**: Find research papers by topic or author
2. **Load Paper + Code**: Download paper and clone associated GitHub repository
3. **Answer Questions**: Ask questions about the paper's code, methodology, or results

## Example Queries

- "Find papers about Graph Neural Networks"
- "Load paper 2103.14030"
- "What is the main architecture used in this paper?"
- "How is the loss function implemented?"

## Expertise

- Machine Learning Research Papers
- Academic Code Repositories
- Paper-to-Code Synthesis
- Implementation Analysis
```

---

## Part 3: Communication Flow

### Message Types

Your Railway agent already handles these messages:

1. **SearchPaperRequest** → SearchPaperResponse
   ```python
   class SearchPaperRequest(Model):
       query: str
       use_gemini: bool = True
       max_results: int = 3
   ```

2. **SelectPaperRequest** → Response
   ```python
   class SelectPaperRequest(Model):
       session_id: str
       selection: int
   ```

3. **InitPaperRequest** → InitPaperResponse
   ```python
   class InitPaperRequest(Model):
       session_id: str
       arxiv_id: str
   ```

4. **ChatRequest** → ChatResponse
   ```python
   class ChatRequest(Model):
       session_id: str
       message: str
   ```

### Session Management

**Challenge:** Hosted agent needs to maintain session state (which paper is loaded, etc.)

**Solutions:**

1. **Simple:** Store session_id in hosted agent's global state
2. **Better:** Use Agentverse storage API (if available)
3. **Best:** Include session context in every message to Railway agent

### "Giving Instructions"

When you ask "how to give instructions", this means:

1. **DeltaV User types:** "Find papers about transformers"
2. **Hosted agent parses:** Intent = "search_paper", Query = "transformers"
3. **Hosted agent sends:** `SearchPaperRequest(query="transformers", use_gemini=True, max_results=3)`
4. **Railway agent receives:** The SearchPaperRequest message
5. **Railway agent processes:** Calls Gemini, returns SearchPaperResponse
6. **Hosted agent receives:** SearchPaperResponse with paper options
7. **Hosted agent formats:** Converts to ChatMessage with text
8. **DeltaV User sees:** "Found 3 papers: 1. Paper Title... 2. ..."

**The "instruction" is the message object itself** - SearchPaperRequest, InitPaperRequest, ChatRequest, etc.

---

## Part 4: Deployment Steps

### Step-by-Step

1. **Deploy to Railway**
   ```bash
   git add .
   git commit -m "Configure Railway deployment"
   git push
   ```

2. **Get Railway Agent Address**
   - Check Railway logs
   - Look for: `Agent address: agent1q...`
   - Copy this address

3. **Create Hosted Agent**
   - Go to Agentverse → Create Hosted Agent
   - Paste the router code above
   - Update `RAILWAY_AGENT_ADDRESS` with copied address
   - Fill out README with search keywords

4. **Start Hosted Agent**
   - Click "Start Agent" in Agentverse
   - Agent will register in Almanac

5. **Test in ASI:One**
   - Go to asi1.ai/chat
   - Enable "Agents" toggle
   - Ask: "Connect me to an agent that helps with research papers"
   - Your agent should appear
   - Click "Chat with Agent"

---

## Part 5: Limitations & Improvements

### Current Limitations

1. **No Response Handling:** The hosted agent sends requests but doesn't properly handle responses from Railway
2. **Session Management:** Simplified session ID handling
3. **Error Handling:** Basic error messages

### Improvements Needed

1. **Add Response Handlers:**
   ```python
   @protocol.on_message(SearchPaperResponse)
   async def handle_search_response(ctx: Context, sender: str, msg: SearchPaperResponse):
       # Format search results as ChatMessage
       # Store session_id for future requests
       pass
   ```

2. **Better Session Management:**
   - Store session state in Agentverse storage
   - Map DeltaV users to sessions

3. **Streaming Responses:**
   - For long operations (InitPaper takes 30-60s)
   - Send intermediate updates

4. **Multi-Turn Conversations:**
   - Don't use `EndSessionContent` immediately
   - Maintain conversation context

---

## Part 6: Testing

### Local Testing

1. **Test Railway deployment locally:**
   ```bash
   # In one terminal
   python backend/src/agent.py

   # In another terminal
   python backend/api_server.py
   ```

2. **Test hosted agent locally:**
   ```bash
   python test_agent_local.py
   ```

### Production Testing

1. **Railway health check:**
   ```
   curl https://your-app.railway.app/health
   ```

2. **Agent registration:**
   - Check Railway logs for agent address
   - Verify in Agentverse dashboard

3. **End-to-end test:**
   - Use ASI:One chat
   - Search for your agent
   - Send test queries

---

## Troubleshooting

### Agent Not Appearing in ASI:One

1. Check README has good keywords
2. Verify agent is running in Agentverse
3. Wait 5-10 minutes for indexing

### Railway Agent Not Responding

1. Check Railway logs for errors
2. Verify `RAILWAY_PUBLIC_DOMAIN` is set correctly
3. Test agent endpoint: `https://your-app.railway.app/submit`

### Hosted Agent Errors

1. Check Agentverse terminal for logs
2. Verify `RAILWAY_AGENT_ADDRESS` is correct
3. Ensure Railway agent is running

### Session Issues

1. Session ID not being maintained
2. User asks question but no paper loaded
3. Need better session management (see improvements above)

---

## Summary

**What You Now Have:**

1. ✅ Both Flask API and uAgents agent running on Railway
2. ✅ Agent accessible via AgentVerse mailbox
3. ✅ Template for hosted agent router
4. ✅ Clear communication flow

**What You Need To Do:**

1. Deploy to Railway
2. Get Railway agent address from logs
3. Create hosted agent in Agentverse with that address
4. Test in ASI:One

**Result:**

Users can discover and interact with Repo Rover through DeltaV/ASI:One, while all heavy processing (ChromaDB, Git, file system, 30-60 second operations) happens on your Railway infrastructure.

---

## Next Steps

1. **Deploy to Railway** and get agent address
2. **Create hosted agent** in Agentverse
3. **Test the flow** in ASI:One
4. **Improve response handling** (add handlers for SearchPaperResponse, etc.)
5. **Add session management** for multi-turn conversations

Let me know when you've deployed to Railway and I can help with the hosted agent implementation!
