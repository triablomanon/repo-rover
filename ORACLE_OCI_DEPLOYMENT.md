# ☁️ Oracle OCI Deployment Guide - Always Free Tier

Deploy your Repo Rover agent to Oracle Cloud Infrastructure using their generous **Always Free** tier.

---

## 🎁 Oracle OCI Free Tier (Best Free Tier!)

Oracle offers the **BEST free tier** among all cloud providers:

### What You Get Forever (No Time Limit):

**Compute:**
- ✅ **2 AMD-based VMs** (1/8 OCPU, 1 GB memory each)
- ✅ **OR 4 Arm-based VMs** (1 OCPU, 6 GB memory each) ⭐ **BEST VALUE**
- ✅ **Ampere A1 Compute** (up to 4 cores + 24GB RAM total)

**Storage:**
- ✅ **200 GB Block Volume**
- ✅ **10 GB Object Storage**

**Network:**
- ✅ **10 TB outbound data transfer/month**
- ✅ **Load Balancer** (10 Mbps)

### Comparison with Other Free Tiers:

| Provider | Free Compute | RAM | Storage | Duration |
|----------|-------------|-----|---------|----------|
| **Oracle OCI** | 4 CPUs | 24 GB | 200 GB | ✅ **Forever** |
| AWS | 1 CPU | 1 GB | 30 GB | ❌ 12 months |
| Google Cloud | 1 CPU | 0.6 GB | 30 GB | ❌ 90 days |
| Azure | 1 CPU | 1 GB | 64 GB | ❌ 12 months |
| Railway | Variable | Variable | 1 GB | ✅ Forever |
| Heroku | 1 CPU | 512 MB | - | ❌ Deprecated |

**Winner: Oracle OCI** 🏆 (Most resources, truly free forever)

---

## 🚀 Deploy Repo Rover to Oracle OCI - Step by Step

### Prerequisites:
- Oracle Cloud account (free, requires credit card for verification but won't charge)
- Your Repo Rover code
- Your GEMINI_API_KEY

**Estimated Time:** 30-45 minutes

---

## 📋 Part 1: Create Oracle Cloud Account

### Step 1: Sign Up

1. Go to https://www.oracle.com/cloud/free/
2. Click **"Start for free"**
3. Fill in details:
   - Email address
   - Country/Region
   - Cloud Account Name (unique, e.g., "reporover123")
4. **Credit card required** (for verification only, won't charge)
5. Verify email and phone

### Step 2: Verify Account

- Check email for verification link
- Complete phone verification
- Account creation takes ~5 minutes

---

## 🖥️ Part 2: Create VM Instance (Ampere A1)

### Step 1: Navigate to Compute

1. Log in to Oracle Cloud Console
2. Click **☰ Menu** → **Compute** → **Instances**
3. Click **"Create Instance"**

### Step 2: Configure Instance

**Name:**
```
repo-rover-agent
```

**Image and Shape:**
1. Click **"Change Image"**
   - Select: **Ubuntu 22.04 Minimal**
   - Click **"Select Image"**

2. Click **"Change Shape"**
   - Select: **Ampere (ARM-based)**
   - Shape: **VM.Standard.A1.Flex**
   - **OCPU count:** 2 (or up to 4 if you want)
   - **Memory (GB):** 12 (or up to 24 if you want)
   - This is **FREE!** ✅
   - Click **"Select Shape"**

**Networking:**
- Use default VCN (Virtual Cloud Network)
- ✅ Check **"Assign a public IPv4 address"**

**Add SSH Keys:**
- Select **"Generate a key pair for me"**
- Click **"Save Private Key"** (important! save to safe location)
- Click **"Save Public Key"**

**Boot Volume:**
- Keep default (50 GB is plenty)

### Step 3: Create Instance

1. Review settings
2. Click **"Create"**
3. Wait ~2 minutes for provisioning
4. **Copy the Public IP address** shown

---

## 🔐 Part 3: Configure Firewall

Oracle has two layers of firewall. You need to open both.

### Step 1: Security List (Cloud Firewall)

1. In your instance page, click your **VCN name** (usually "vcn-...")
2. Click **"Security Lists"** on left
3. Click **"Default Security List for vcn-..."**
4. Click **"Add Ingress Rules"**

**Add these rules:**

**Rule 1: HTTP (for Inspector)**
- Source CIDR: `0.0.0.0/0`
- IP Protocol: `TCP`
- Destination Port Range: `8001`
- Description: `Agent Inspector`

Click **"Add Ingress Rules"**

### Step 2: Instance Firewall (iptables)

We'll configure this after connecting to the instance.

---

## 🔌 Part 4: Connect to Your Instance

### Option A: Windows (PowerShell)

```powershell
# Navigate to where you saved the private key
cd C:\Users\YourName\Downloads

# Set correct permissions
icacls .\ssh-key-*.key /inheritance:r
icacls .\ssh-key-*.key /grant:r "%USERNAME%":"(R)"

# Connect (replace with your IP)
ssh -i ssh-key-*.key ubuntu@YOUR_PUBLIC_IP
```

### Option B: Mac/Linux

```bash
# Navigate to key location
cd ~/Downloads

# Set correct permissions
chmod 400 ssh-key-*.key

# Connect (replace with your IP)
ssh -i ssh-key-*.key ubuntu@YOUR_PUBLIC_IP
```

**First time:** Type `yes` when asked about fingerprint

You should now see:
```
ubuntu@repo-rover-agent:~$
```

---

## 📦 Part 5: Install Dependencies

### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Python and Git

```bash
sudo apt install -y python3.10 python3-pip git
```

### Step 3: Install System Dependencies

```bash
# For ChromaDB
sudo apt install -y build-essential

# For Git operations
sudo apt install -y git-all
```

### Step 4: Configure Firewall (iptables)

```bash
# Allow port 8001 for Agent Inspector
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8001 -j ACCEPT
sudo netfilter-persistent save
```

If `netfilter-persistent` not found:
```bash
sudo apt install -y iptables-persistent
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

---

## 📥 Part 6: Deploy Your Agent

### Step 1: Clone Your Repository

```bash
# If your repo is public:
git clone https://github.com/yourusername/repo-rover.git
cd repo-rover

# If private, set up GitHub SSH key first
```

### Step 2: Install Python Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

**Create requirements.txt if you don't have it:**
```bash
pip3 install uagents flask flask-cors arxiv google-generativeai chromadb python-dotenv rich
pip3 freeze > requirements.txt
```

### Step 3: Configure Environment Variables

```bash
nano .env
```

**Add:**
```bash
GEMINI_API_KEY=your_actual_key_here
FETCHAI_AGENT_SEED=arxini_research_code_companion_seed
CHROMA_PATH=/home/ubuntu/repo-rover/backend/chroma_db
REPO_CLONE_DIR=/home/ubuntu/repo-rover/backend/cloned_repos
```

**Save:** Ctrl+X, Y, Enter

### Step 4: Create Directories

```bash
mkdir -p chroma_db cloned_repos papers cache cache/concept_maps
```

---

## 🚀 Part 7: Run Agent with Systemd (Auto-Start)

### Step 1: Create Systemd Service

```bash
sudo nano /etc/systemd/system/repo-rover-agent.service
```

**Add:**
```ini
[Unit]
Description=Repo Rover Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/repo-rover/backend
Environment="PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /home/ubuntu/repo-rover/backend/src/agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Save:** Ctrl+X, Y, Enter

### Step 2: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable repo-rover-agent

# Start service
sudo systemctl start repo-rover-agent

# Check status
sudo systemctl status repo-rover-agent
```

**You should see:**
```
● repo-rover-agent.service - Repo Rover Agent
   Active: active (running)
```

### Step 3: View Logs

```bash
# View real-time logs
sudo journalctl -u repo-rover-agent -f

# View recent logs
sudo journalctl -u repo-rover-agent -n 100
```

**Look for:**
```
🚀 REPO ROVER AGENT 🚀
📍 Agent Address: agent1q...
✅ Agent is running and ready to receive requests...
🔍 Local Agent Inspector:
   http://YOUR_IP:8001/
```

---

## 🌐 Part 8: Access Agent Inspector

### Open in Browser:

```
http://YOUR_PUBLIC_IP:8001/
```

You should see the **Local Agent Inspector** UI!

### Connect to AgentVerse:

1. In Inspector, click **"Connect to Agentverse"**
2. Follow the prompts
3. Your agent will appear in AgentVerse dashboard as 🟢 **Online**

---

## 🔄 Part 9: Managing Your Agent

### Common Commands:

```bash
# View status
sudo systemctl status repo-rover-agent

# View logs (live)
sudo journalctl -u repo-rover-agent -f

# Restart agent
sudo systemctl restart repo-rover-agent

# Stop agent
sudo systemctl stop repo-rover-agent

# Start agent
sudo systemctl start repo-rover-agent

# View recent logs
sudo journalctl -u repo-rover-agent -n 100 --no-pager
```

### Update Agent Code:

```bash
# Stop agent
sudo systemctl stop repo-rover-agent

# Pull latest code
cd /home/ubuntu/repo-rover
git pull

# Install new dependencies if any
cd backend
pip3 install -r requirements.txt

# Restart agent
sudo systemctl start repo-rover-agent
```

---

## 📊 Part 10: Monitor Resources

### Check Memory Usage:

```bash
free -h
```

### Check Disk Usage:

```bash
df -h
```

### Check CPU Usage:

```bash
top
# Press 'q' to quit
```

### Agent Process:

```bash
ps aux | grep agent.py
```

---

## 🎯 Optional: Deploy API Server Too

You can run both the agent AND the API server on the same instance!

### Step 1: Create API Service

```bash
sudo nano /etc/systemd/system/repo-rover-api.service
```

**Add:**
```ini
[Unit]
Description=Repo Rover API Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/repo-rover/backend
Environment="PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /home/ubuntu/repo-rover/backend/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 2: Open Port 5000

**In OCI Console (Security List):**
- Add Ingress Rule for port 5000 (same as port 8001)

**On Instance:**
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 5000 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

### Step 3: Start API

```bash
sudo systemctl enable repo-rover-api
sudo systemctl start repo-rover-api
```

Now you have:
- **Agent:** Running on port 8001
- **API:** Running on port 5000
- **Both on same free instance!**

---

## 🌐 Optional: Add Domain Name

### Using Cloudflare (Free):

1. **Buy domain** (Namecheap, ~$10/year)
2. **Add to Cloudflare** (free plan)
3. **Create A record:**
   - Name: `agent` (or `@` for root)
   - IPv4 address: `YOUR_OCI_PUBLIC_IP`
   - Proxy: Off (orange cloud off)

Access via: `http://agent.yourdomain.com:8001`

### Using Oracle DNS (Free):

Oracle provides free DNS with your account. Check OCI docs for setup.

---

## 💰 Cost Breakdown

### Oracle OCI Always Free Tier:

**What you're using:**
- VM.Standard.A1.Flex (2 OCPU, 12 GB RAM)
- 50 GB Boot Volume
- Public IP
- 10 TB bandwidth/month

**Cost:** **$0.00** ✅ **Forever!**

**Comparison to paid hosting:**
- AWS t3.medium (2 vCPU, 4 GB): **~$30/month**
- DigitalOcean (2 vCPU, 4 GB): **$24/month**
- Railway Hobby: **$5/month** (500 hours)

**You save:** **$30/month** with OCI free tier!

---

## 🔐 Security Best Practices

### 1. Update Regularly:

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Configure UFW (Firewall):

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8001/tcp
sudo ufw allow 5000/tcp
sudo ufw enable
```

### 3. Disable Root SSH:

```bash
sudo nano /etc/ssh/sshd_config
```

Find and set:
```
PermitRootLogin no
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

### 4. Setup Fail2ban:

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 🐛 Troubleshooting

### Issue: Cannot access Inspector on port 8001

**Solution:**
```bash
# Check if agent is running
sudo systemctl status repo-rover-agent

# Check if port is open
sudo netstat -tlnp | grep 8001

# Check iptables
sudo iptables -L -n | grep 8001

# Check OCI Security List in console
```

### Issue: Agent not connecting to AgentVerse

**Solution:**
```bash
# Check logs
sudo journalctl -u repo-rover-agent -n 50

# Make sure .env has correct values
cat /home/ubuntu/repo-rover/backend/.env

# Check internet connectivity
ping -c 3 google.com
```

### Issue: Out of memory

**Solution:**
```bash
# Check memory
free -h

# If low, create swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Issue: Disk full

**Solution:**
```bash
# Check disk usage
df -h

# Find large directories
sudo du -h --max-depth=1 / | sort -hr | head -20

# Clean up
sudo apt autoremove -y
sudo apt clean
```

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Can SSH into instance
- [ ] Agent systemd service is running (`sudo systemctl status repo-rover-agent`)
- [ ] Can access Inspector at `http://PUBLIC_IP:8001`
- [ ] Agent appears in AgentVerse dashboard
- [ ] Agent shows as 🟢 Online
- [ ] Can send test message via AgentVerse
- [ ] Logs show no errors (`sudo journalctl -u repo-rover-agent -f`)
- [ ] Agent auto-restarts after reboot (`sudo reboot` then check)

---

## 🎉 Success!

You now have:
- ✅ Repo Rover agent running 24/7 on Oracle Cloud
- ✅ Completely free (Oracle Always Free tier)
- ✅ 2 CPUs + 12 GB RAM (better than most paid options!)
- ✅ Auto-starts on boot
- ✅ Accessible in AgentVerse
- ✅ Can optionally run API server too

**For your hackathon:**
- Agent is always online
- Accessible from anywhere
- Professional deployment
- Zero cost!

---

## 📚 Additional Resources

**Oracle Cloud:**
- Free Tier: https://www.oracle.com/cloud/free/
- Documentation: https://docs.oracle.com/en-us/iaas/
- Ampere A1: https://www.oracle.com/cloud/compute/arm/

**Tutorials:**
- OCI Getting Started: https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/signingup.htm
- Compute Instances: https://docs.oracle.com/en-us/iaas/Content/Compute/home.htm

---

**Your Oracle OCI instance is superior to Railway/Heroku for this use case!** 🚀

**Want me to walk you through the setup step-by-step?**
