# Testing Guide

## ✅ Fixed Issues

### 1. Gemini API Updated
- Now uses `google-genai` package (new SDK)
- Direct PDF processing with multimodal API
- No need for PyPDF2 text extraction

### 2. Shows Gemini's Response
- Full response printed to console
- See exactly what Gemini finds in the PDF

### 3. Individual Testing Added
- Test one component at a time
- Faster debugging

---

## 🔧 Update Your Environment

```bash
conda activate repo-rover
conda env update -f environment.yml --prune
```

This installs the new `google-genai` package.

---

## 🧪 Individual Testing

### Use `test_individual.py`

```bash
# Test specific components
python test_individual.py config   # Check API keys
python test_individual.py corpus   # Test corpus manager
python test_individual.py paper    # Test paper finder  
python test_individual.py repo     # Test repo finder (see Gemini output!)
python test_individual.py gemini   # Ask Gemini custom questions

# Run all tests
python test_individual.py all
```

---

## 📄 See What Gemini Says

### Test Repo Finder (shows full response)
```bash
python test_individual.py repo
```

**Output:**
```
[2/3] Analyzing PDF with Gemini...
Analyzing PDF with Gemini: 2310.02170.pdf

Gemini's response:
https://github.com/SALT-NLP/DyLAN

✓ Extracted URL: https://github.com/SALT-NLP/DyLAN
```

You'll see:
- What Gemini extracted from the PDF
- The exact GitHub URL it found
- Any errors or issues

---

## ✏️ Change Questions to Gemini

### For Repo Finder
Edit `src/discovery/repo_finder.py` line 72-82:

```python
prompt = """YOUR CUSTOM PROMPT HERE

Ask Gemini to find something else in the PDF!
"""
```

### Test Your Changes
```bash
python test_individual.py repo
```

---

## 🎯 Custom Gemini Questions

Want to ask Gemini about code? Use the interactive test:

```bash
python test_individual.py gemini
```

Then type your question:
```
What would you like to ask Gemini about code?
Your question: How does the attention mechanism work?

Gemini's response:
----------------------------------------------------------------------
The attention mechanism computes similarity scores...
----------------------------------------------------------------------
```

---

## 📊 Test Individual Components

| Component | Command | What It Tests |
|-----------|---------|---------------|
| Config | `python test_individual.py config` | API keys loaded |
| Corpus | `python test_individual.py corpus` | Vectara corpus creation |
| Paper | `python test_individual.py paper` | ArXiv download |
| Repo | `python test_individual.py repo` | Gemini PDF analysis |
| Gemini | `python test_individual.py gemini` | Custom questions |

---

## 🔍 Debugging Workflow

1. **Check config first:**
   ```bash
   python test_individual.py config
   ```

2. **Test repo finder with output:**
   ```bash
   python test_individual.py repo
   ```

3. **See Gemini's raw response** in the console

4. **Adjust prompt** in `repo_finder.py` if needed

5. **Test again** until it works

---

## 📝 Example Session

```bash
$ python test_individual.py repo

======================================================================
TEST: Repo Finder (with Gemini response)
======================================================================

[1/3] Getting paper and PDF...
✓ PDF: ./papers/2310.02170.pdf

[2/3] Analyzing PDF with Gemini...
Analyzing PDF with Gemini: 2310.02170.pdf

Gemini's response:
https://github.com/SALT-NLP/DyLAN

✓ Extracted URL: https://github.com/SALT-NLP/DyLAN

[3/3] Result:
✅ Found: https://github.com/SALT-NLP/DyLAN
```

---

## 🚀 Quick Commands

```bash
# Update environment
conda env update -f environment.yml --prune

# Test repo finder only
python test_individual.py repo

# Ask custom question
python test_individual.py gemini

# Run all tests
python test.py
```

---

## ⚠️ Common Issues

**"Import google.genai could not be resolved"**
- IDE warning, ignore it
- Will work at runtime after installing package

**"GEMINI_API_KEY not found"**
- Check `.env` file exists
- Verify API key is correct

**"No GitHub URL found"**
- Check what Gemini said (printed to console)
- Try adjusting the prompt
- Use fallback repos

---

Ready to test with multimodal Gemini! 🎉
