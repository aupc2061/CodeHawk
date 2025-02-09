import os
import dotenv
from code_agent.config import GOOGLE_API_KEY, GROQ_API_KEY

# Load environment variables
dotenv.load_dotenv()
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

from .core import CodeStructureAnalyzer
# from .code_analyzer import parse_python_file, create_structure
from .code_walker import find_src_files, filter_important_files
from .progress import Spinner
from .repo_mapper import Tag, get_ranked_tags
from .tree_context import TreeContext, to_tree, render_tree

__all__ = [
    'CodeStructureAnalyzer',
    'parse_python_file',
    'create_structure',
    'find_src_files',
    'filter_important_files',
    'Spinner',
    'Tag',
    'get_ranked_tags',
    'TreeContext',
    'to_tree',
    'render_tree'
]