import os
from typing import List, Set
from pathlib import Path

ROOT_IMPORTANT_FILES = [
    # Version Control
    ".gitignore", ".gitattributes",
    # Documentation
    "README", "README.md", "README.txt", "README.rst",
    "CONTRIBUTING", "CONTRIBUTING.md", "CONTRIBUTING.txt", "CONTRIBUTING.rst",
    "LICENSE", "LICENSE.md", "LICENSE.txt",
    "CHANGELOG", "CHANGELOG.md", "CHANGELOG.txt", "CHANGELOG.rst",
    "SECURITY", "SECURITY.md", "SECURITY.txt", "CODEOWNERS",
    # Package Management and Dependencies
    "requirements.txt", "Pipfile", "Pipfile.lock", "pyproject.toml",
    "setup.py", "setup.cfg", "package.json", "package-lock.json",
    "yarn.lock", "npm-shrinkwrap.json", "Gemfile", "Gemfile.lock",
    "composer.json", "composer.lock", "pom.xml", "build.gradle",
    "build.sbt", "go.mod", "go.sum", "Cargo.toml", "Cargo.lock",
    "mix.exs", "rebar.config", "project.clj", "Podfile", "Cartfile",
    "dub.json", "dub.sdl"
]

# Normalize the lists once
NORMALIZED_ROOT_IMPORTANT_FILES = set(os.path.normpath(path) for path in ROOT_IMPORTANT_FILES)

def is_important(file_path: str) -> bool:
    """Check if a file is considered important based on predefined patterns."""
    file_name = os.path.basename(file_path)
    dir_name = os.path.normpath(os.path.dirname(file_path))
    normalized_path = os.path.normpath(file_path)

    # Check for GitHub Actions workflow files
    if dir_name == os.path.normpath(".github/workflows") and file_name.endswith(".yml"):
        return True

    return normalized_path in NORMALIZED_ROOT_IMPORTANT_FILES

def filter_important_files(file_paths: List[str]) -> List[str]:
    """Filter a list of file paths to return only those that are commonly important in codebases."""
    return list(filter(is_important, file_paths))

def find_src_files(directory: str) -> List[str]:
    """Find all source files in a directory recursively."""
    if not os.path.isdir(directory):
        return [directory]

    src_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            src_files.append(os.path.join(root, file))
    return src_files