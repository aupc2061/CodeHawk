import os
import dotenv
from pathlib import Path

# Load environment variables
dotenv_path = Path('.env')
if not dotenv_path.exists():
    print("Warning: .env file not found. Please create one with GOOGLE_API_KEY and GROQ_API_KEY.")
    print("See README.md for setup instructions.")
else:
    dotenv.load_dotenv()

# Get API keys with validation
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "YOUR API KEY":
    print("Warning: Valid GOOGLE_API_KEY not found in environment variables")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY or GROQ_API_KEY == "YOUR API KEY":
    print("Warning: Valid GROQ_API_KEY not found in environment variables")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "YOUR API KEY":
    print("Warning: Valid ANTHROPIC_API_KEY not found in environment variables")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY or ""
os.environ["GROQ_API_KEY"] = GROQ_API_KEY or ""
os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY or ""

from .core import CodeStructureAnalyzer
from .code_walker import find_src_files, filter_important_files
from .progress import Spinner
from .repo_mapper import Tag, get_ranked_tags
from .tree_context import TreeContext, to_tree, render_tree

__all__ = [
    'CodeStructureAnalyzer',
    'find_src_files',
    'filter_important_files',
    'Spinner',
    'Tag',
    'get_ranked_tags',
    'TreeContext',
    'to_tree',
    'render_tree'
]