"""
Individual component testing - Run specific tests

Usage:
  python test_individual.py config
  python test_individual.py corpus
  python test_individual.py paper
  python test_individual.py repo
  python test_individual.py query     <- Ask questions! (skips clone/index if corpus exists)
  python test_individual.py all
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_config():
    """Test 01: Config & Environment"""
    print("\n" + "=" * 70)
    print("TEST: Config & Environment")
    print("=" * 70)

    from utils.config import Config

    print(f"✓ GEMINI_API_KEY: {Config.GEMINI_API_KEY[:20]}...")
    print(f"✓ VECTARA_CUSTOMER_ID: {Config.VECTARA_CUSTOMER_ID}")
    print(f"✓ VECTARA_API_KEY: {Config.VECTARA_API_KEY[:20]}...")
    print("\n✅ Config loaded successfully!")


def test_corpus():
    """Test 02: Corpus Manager"""
    print("\n" + "=" * 70)
    print("TEST: Corpus Manager")
    print("=" * 70)

    from corpus_manager import find_or_create_corpus

    test_corpus = "2310.02170"
    corpus_id = find_or_create_corpus(test_corpus)

    if corpus_id:
        print(f"\n✅ Corpus ID: {corpus_id}")
        return corpus_id
    else:
        print("\n❌ Failed to get corpus")
        return None


def test_paper():
    """Test 03: Paper Finder"""
    print("\n" + "=" * 70)
    print("TEST: Paper Finder")
    print("=" * 70)

    from discovery.paper_finder import PaperFinder

    finder = PaperFinder()
    paper = finder.analyze_paper("2310.02170", download=True)

    if paper and paper.get('pdf_path'):
        print(f"✓ Title: {paper['title'][:60]}...")
        print(f"✓ ArXiv ID: {paper['arxiv_id']}")
        print(f"✓ PDF: {paper['pdf_path']}")
        print(f"\n✅ Paper found and downloaded!")
        return paper
    else:
        print("\n❌ Failed to find/download paper")
        return None


def test_repo():
    """Test 04: Repo Finder with Gemini output"""
    print("\n" + "=" * 70)
    print("TEST: Repo Finder (with Gemini response)")
    print("=" * 70)

    from discovery.paper_finder import PaperFinder
    from discovery.repo_finder import RepoFinder
    from pathlib import Path

    print("\n[1/3] Getting paper and PDF...")
    finder = PaperFinder()
    paper = finder.analyze_paper("2310.02170", download=True)

    if not paper or not paper.get('pdf_path'):
        print("❌ No paper/PDF found")
        return None

    print(f"✓ PDF: {paper['pdf_path']}")

    print("\n[2/3] Analyzing PDF with Gemini...")
    repo_finder = RepoFinder()
    pdf_path = Path(paper['pdf_path'])

    repo_url = repo_finder.extract_github_from_pdf(pdf_path)

    print("\n[3/3] Result:")
    if repo_url:
        print(f"✅ Found: {repo_url}")
        return repo_url
    else:
        print("⚠️  Gemini didn't find URL, trying fallback...")
        repo_url = repo_finder.find_with_fallback(paper)
        if repo_url:
            print(f"✅ Fallback found: {repo_url}")
            return repo_url
        else:
            print("❌ No repo found")
            return None


def test_query():
    """Test FULL pipeline: Vectara search + Gemini with PDF context"""
    print("\n" + "=" * 70)
    print("TEST: Full Query Pipeline (Vectara + PDF + Gemini)")
    print("=" * 70)

    from discovery.paper_finder import PaperFinder
    from discovery.repo_finder import RepoFinder
    from utils.repo_utils import RepoAnalyzer
    from utils.config import Config
    from understanding.code_indexer import VectaraIndexer
    from understanding.gemini_synthesizer import GeminiSynthesizer
    from understanding.query_pipeline import QueryPipeline
    from corpus_manager import find_or_create_corpus, corpus_has_documents

    # Step 1: Get corpus
    print("\n[1/4] Getting corpus...")
    corpus_id = find_or_create_corpus("2310.02170")
    if not corpus_id:
        print("❌ Failed to get corpus")
        return
    print(f"✓ Corpus ID: {corpus_id}")

    # Step 2: Get paper and PDF
    print("\n[2/4] Getting paper and PDF...")
    paper_finder = PaperFinder()
    paper = paper_finder.analyze_paper("2310.02170", download=True)
    if not paper or not paper.get('pdf_path'):
        print("❌ No paper/PDF")
        return
    print(f"✓ PDF: {paper['pdf_path']}")

    # Step 3: Check if corpus already has documents
    print("\n[3/4] Checking if corpus has code indexed...")
    has_docs = corpus_has_documents(corpus_id)

    indexer = VectaraIndexer(
        Config.VECTARA_CUSTOMER_ID,
        Config.VECTARA_API_KEY,
        corpus_id
    )

    repo_path = None

    if has_docs:
        print("✓ Corpus already has indexed code - skipping clone & indexing")
    else:
        print("⚠ Corpus is empty - need to clone repo and index code")

        # Get repository
        print("\n  [3a] Getting repository...")
        repo_finder = RepoFinder()
        repo_url = repo_finder.find_with_fallback(paper)
        if not repo_url:
            print("  ❌ No repo found")
            return
        print(f"  ✓ Repo: {repo_url}")

        # Clone repo
        print("\n  [3b] Cloning repository...")
        analyzer = RepoAnalyzer(Config.REPO_CLONE_DIR)
        repo_path = analyzer.clone_repository(repo_url)
        if not repo_path:
            print("  ❌ Failed to clone")
            return
        print(f"  ✓ Cloned to: {repo_path}")

        # Index code
        print("\n  [3c] Indexing code (this may take a minute)...")
        count = indexer.index_repository(repo_path, "dylan")
        print(f"  ✓ Indexed {count} files")

    # Step 4: Initialize pipeline
    print("\n[4/4] Initializing query pipeline...")
    gemini = GeminiSynthesizer(Config.GEMINI_API_KEY)

    # If we didn't clone, we don't have repo_path/readme/structure
    # But we don't need them for querying!
    pipeline = QueryPipeline(indexer, gemini, paper, repo_path)

    if repo_path:
        analyzer = RepoAnalyzer(Config.REPO_CLONE_DIR)
        repo_structure = analyzer.get_repo_structure(repo_path)
        readme = analyzer.get_readme_content(repo_path)
        pipeline.initialize(readme or "", repo_structure)
    else:
        # Initialize with minimal context
        pipeline.initialize("", {})

    # Ask question
    print("\n" + "=" * 70)
    print("ASK YOUR QUESTION")
    print("=" * 70)
    print("\nThe pipeline will:")
    print("  1. Search Vectara for relevant code snippets")
    print("  2. Provide Gemini with: PDF + code + your question")
    print("  3. Return an answer connecting paper theory to code")

    question = input("\nYour question: ").strip()
    if not question:
        question = "What is the main contribution of this paper?"

    print(f"\n🔍 Searching Vectara for: '{question}'")
    print(f"📄 Loading paper PDF...")
    print(f"🤖 Asking Gemini with full context...\n")

    response = pipeline.query(question)

    print("\n" + "=" * 70)
    print("ANSWER")
    print("=" * 70)
    print(response['answer'])
    print("\n" + "=" * 70)
    print(f"✓ Confidence: {response['confidence']}")
    print(f"✓ Based on {response['num_sources']} code sources from Vectara")
    print(f"✓ Used paper PDF for context")
    print("=" * 70)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    test_name = sys.argv[1].lower()

    tests = {
        'config': test_config,
        'corpus': test_corpus,
        'paper': test_paper,
        'repo': test_repo,
        'query': test_query,
    }

    if test_name == 'all':
        for name, test_func in tests.items():
            if name != 'query':  # Skip query (interactive)
                test_func()
    elif test_name in tests:
        tests[test_name]()
    else:
        print(f"Unknown test: {test_name}")
        print(__doc__)


if __name__ == "__main__":
    main()
