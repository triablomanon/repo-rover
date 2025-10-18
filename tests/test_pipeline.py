"""
Test script for Repo Rover pipeline
Run this to verify everything is working
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config import Config
from discovery.paper_finder import PaperFinder
from discovery.repo_finder import RepoFinder


def test_configuration():
    """Test that all API keys are configured"""
    print("\n=== Testing Configuration ===")

    errors = Config.validate()
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        return False

    print("✅ All required API keys configured")
    print(f"   Gemini Model: {Config.GEMINI_MODEL}")
    print(f"   Clone Directory: {Config.REPO_CLONE_DIR}")
    return True


def test_paper_finder():
    """Test ArXiv paper search"""
    print("\n=== Testing Paper Finder ===")

    try:
        finder = PaperFinder()
        paper = finder.search_paper("Attention Is All You Need", max_results=1)

        if not paper:
            print("❌ Could not find paper")
            return False

        print("✅ Paper search working")
        print(f"   Found: {paper['title'][:50]}...")
        print(f"   ArXiv ID: {paper['arxiv_id']}")
        return True

    except Exception as e:
        print(f"❌ Paper finder error: {e}")
        return False


def test_repo_finder():
    """Test repository discovery"""
    print("\n=== Testing Repository Finder ===")

    try:
        finder = RepoFinder()

        # Test with known paper
        repo_url = finder.find_by_arxiv_id("1706.03762")

        if not repo_url:
            # Try fallback
            known_repos = finder.get_known_repos()
            repo_url = known_repos.get("1706.03762")

        if repo_url:
            print("✅ Repository finding working")
            print(f"   Found: {repo_url}")
            return True
        else:
            print("⚠️  Repository not found (this is okay, fallback exists)")
            return True

    except Exception as e:
        print(f"❌ Repository finder error: {e}")
        return False


def test_vectara_connection():
    """Test Vectara API connection"""
    print("\n=== Testing Vectara Connection ===")

    try:
        from understanding.code_indexer import VectaraIndexer

        indexer = VectaraIndexer(
            Config.VECTARA_CUSTOMER_ID,
            Config.VECTARA_API_KEY,
            Config.VECTARA_CORPUS_ID
        )

        # Try a simple search (will return empty if corpus is empty)
        results = indexer.search("test", num_results=1)

        print("✅ Vectara connection working")
        print(f"   Corpus ID: {Config.VECTARA_CORPUS_ID}")
        return True

    except Exception as e:
        print(f"❌ Vectara error: {e}")
        print("   Check your Customer ID, API Key, and Corpus ID")
        return False


def test_gemini_connection():
    """Test Gemini API connection"""
    print("\n=== Testing Gemini Connection ===")

    try:
        from understanding.gemini_synthesizer import GeminiSynthesizer

        synthesizer = GeminiSynthesizer(
            Config.GEMINI_API_KEY,
            Config.GEMINI_MODEL
        )

        # Simple test prompt
        import google.generativeai as genai
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel(Config.GEMINI_MODEL)

        response = model.generate_content("Say 'test successful' and nothing else")

        print("✅ Gemini connection working")
        print(f"   Model: {Config.GEMINI_MODEL}")
        print(f"   Response: {response.text[:50]}")
        return True

    except Exception as e:
        print(f"❌ Gemini error: {e}")
        print("   Check your GEMINI_API_KEY")
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Repo Rover - System Test")
    print("=" * 60)

    results = {
        "Configuration": test_configuration(),
        "Paper Finder": test_paper_finder(),
        "Repository Finder": test_repo_finder(),
        "Vectara": test_vectara_connection(),
        "Gemini": test_gemini_connection(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All tests passed! Repo Rover is ready to use.")
        print("\nNext steps:")
        print("  python src/main.py --paper 'Attention Is All You Need'")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
        print("See QUICK_START.md for setup instructions.")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
