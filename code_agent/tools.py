import os
import ast
from typing import Optional
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Optional

@tool
def get_class_info(relative_file_path: str, class_name: str, structure: Dict) -> Optional[str]:
    """Search for a class by name in the given relative file path and return its details."""
    path_parts = relative_file_path.replace("\\", "/").split("/")  # Split into components
    current_level = structure  # Start traversing from the root of the structure
    # Traverse the structure using the normalized path
    for part in path_parts:
        if part in current_level:
            current_level = current_level[part]

    for clazz in current_level["classes"]:
        if clazz["name"] == class_name:
            return clazz['text']
    return None

@tool
def get_function_info(relative_file_path: str, function_name: str, structure: Dict) -> Optional[str]:
    """Search for a function or class method by name in the given relative file path and return its details."""
    path_parts = relative_file_path.replace("\\", "/").split("/")  # Split into components
    current_level = structure
    for part in path_parts:
        if part in current_level:
            current_level = current_level[part]

    for func in current_level["functions"]:
        if func["name"] == function_name:
            return func['text']
    for clazz in current_level["classes"]:
        for method in clazz["methods"]:
            if method["name"] == function_name:
                return method['text']
    return None

def format_class_and_function_info(info: Dict) -> str:
    """
    Format the class and function information as a string representation of the file content.
    
    :param info: dict, The dictionary containing class and function information for a file
    :return: str, Formatted string representation of the class and function structure with line numbers
    """
    result = []

    # Format classes
    if 'classes' in info:
        for cls in info['classes']:
            result.append(f"class {cls['name']} (Lines {cls['start_line']}-{cls['end_line']}):")
            for method in cls.get('methods', []):
                result.append(f"    {method['signature']} (Lines {method['start_line']}-{method['end_line']}):")

    # Format functions
    if 'functions' in info:
        result.append("\n")
        for func in info['functions']:
            result.append(f"def {func['name']}{func['signature'][func['signature'].find('('):]} (Lines {func['start_line']}-{func['end_line']}) :")
    return "\n".join(result)

@tool
def get_class_and_function_info(relative_file_path: str, structure: Dict) -> Optional[str]:
    """
    Retrieves class and function info from the repo map for a given relative file path.
    
    :param relative_file_path: str, The relative file path to look up in the structure
    :param structure: dict, The repository structure dictionary
    :return: dict, Information about the file's classes and functions, or None if not found
    """
    path_parts = relative_file_path.replace("\\", "/").split("/")  # Split into components
    current_level = structure

    # Traverse the structure using the normalized path
    for part in path_parts:
        if part in current_level:
            current_level = current_level[part]
        else:
            return None  # Return None if any part is not found

    return format_class_and_function_info(current_level)  # Return the final value if traversal is successful

@tool
def get_repo_tree(repo_path: str = None) -> str:
    """
    Generates and returns the repository directory tree.

    Args:
        repo_path (str, optional): Path to the repository.
                                   If None, uses the current working directory.

    Returns:
        str: The repository tree or an error message.
    """
    try:
        repo_path = repo_path or os.getcwd()
        tree = []
        
        for dirpath, dirnames, filenames in os.walk(repo_path):
            # Skip hidden directories and their contents
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            
            # Get relative path
            rel_path = os.path.relpath(dirpath, repo_path)
            if rel_path != '.':
                tree.append(rel_path)
            # print(tree)
            # Add files
            for file in filenames:
                if not file.startswith('.'):
                    tree.append(os.path.join(rel_path, file))
                    
        # Sort and join paths
        return '\n'.join(sorted(tree))
        
    except Exception as e:
        return f"Error accessing directory '{repo_path}': {str(e)}"


import os
from typing import Optional

@tool
def open_file(relative_file_path: str, line_number: Optional[int] = None) -> None:
    """Opens the file at the given path in the editor with each line prefixed by its line number."""
    try:
        # First try as absolute path
        if os.path.isabs(relative_file_path):
            file_path = relative_file_path
        else:
            # Try relative to current directory
            file_path = os.path.abspath(relative_file_path)
            if not os.path.exists(file_path):
                # Try relative to workspace root if exists
                workspace = os.getenv("WORKSPACE_ROOT", os.getcwd())
                file_path = os.path.join(workspace, relative_file_path)

        print(f"Opening file: {relative_file_path}")
        with open(file_path, "r", encoding="utf-8") as file:
            lines_with_numbers = [
                f"{line_no:2d}: {line.rstrip()}" for line_no, line in enumerate(file, start=1)
            ]
        return "\n".join(lines_with_numbers)
    except FileNotFoundError:
        return f"Error: The file at {file_path} was not found."
    except Exception as e:
        return f"An error occurred: {e}"


@tool
def goto_line(line_number: int) -> None:
    """Moves the window to show the specified line number."""
    print(f"Moving to line {line_number}.")

@tool
def scroll_down() -> None:
    """Moves the window down by 100 lines."""
    print("Scrolling down by 100 lines.")

@tool
def scroll_up() -> None:
    """Moves the window up by 100 lines."""
    print("Scrolling up by 100 lines.")

@tool
def create_file(filename: str, content: str) -> None:
    """Creates and opens a new file with the given name and writes the provided content to it."""
    with open(filename, 'w') as file:
        file.write(content)
    print(f"File '{filename}' created and content written.")

@tool
def edit_file(start_line: int, end_line: int, content: str, filename: str) -> None:
    """
    Edit a file by replacing content between specified lines or adding new content.
    Handles various editing scenarios with robust line number and content management.
    
    Args:
        start_line (int): The line number where the edit should begin (1-based indexing)
                         - For in-file edits: The first line to be replaced
                         - For appending: If > file length, content will be appended
        end_line (int): The line number where the edit should end (1-based indexing)
                       - Must be >= start_line
                       - For single-line insertions: Set equal to start_line
                       - For appending: Ignored when start_line > file length
        content (str): The new content to insert or replace existing content with
                      - Preserves indentation based on surrounding code
                      - Supports both single and multi-line content
                      - Empty lines will be preserved without indentation
        filename (str): Absolute path to the file to edit
                       - Creates new file if it doesn't exist
                       - Supports both UTF-8 and system default encodings
    """
    if not os.path.exists(filename):
        # Create new file if it doesn't exist
        with open(filename, 'w') as file:
            file.write(content)
        print(f"Created new file '{filename}' with content")
        return

    # Read existing content    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        # Fallback to system default encoding if UTF-8 fails
        with open(filename, 'r') as file:
            lines = file.readlines()
            
    total_lines = len(lines)
    
    # Validate inputs
    if start_line < 1:
        print("Error: Start line must be positive")
        return
        
    # Handle empty files
    if total_lines == 0:
        with open(filename, 'w') as file:
            file.write(content + '\n')
        print(f"Added content to empty file '{filename}'")
        return

    # Split content into lines and preserve indentation
    content_lines = content.splitlines()
    
    # Determine indentation from first non-empty line of existing content
    existing_indent = ""
    for line in lines:
        if line.strip():
            existing_indent = line[:len(line) - len(line.lstrip())]
            break
            
    # Case 1: Append to end of file
    if start_line > total_lines:
        # Ensure there's a newline before appending
        if lines and not lines[-1].endswith('\n'):
            lines.append('\n')
            
        # Add content with proper indentation
        for line in content_lines:
            if line.strip():  # Only indent non-empty lines
                lines.append(existing_indent + line + '\n')
            else:
                lines.append('\n')
                
    # Case 2: Insert or replace within file
    else:
        # Adjust end_line if it exceeds file length
        end_line = min(end_line, total_lines)
        
        # Prepare content with proper indentation
        indented_content = []
        for line in content_lines:
            if line.strip():  # Only indent non-empty lines
                indented_content.append(existing_indent + line + '\n')
            else:
                indented_content.append('\n')
                
        # Replace the lines
        lines[start_line-1:end_line] = indented_content
        
    # Write back to file with error handling
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.writelines(lines)
            
        if start_line > total_lines:
            print(f"Appended content to '{filename}'")
        else:
            print(f"Modified lines {start_line} to {end_line} in '{filename}'")
            
    except Exception as e:
        print(f"Error writing to file: {e}")

@tool
def search_dir(search_term: str, dir_path: str = './') -> None:
    """Searches for `search_term` in all files in the given directory."""
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'r', errors='ignore') as f:
                if search_term in f.read():
                    print(f"Found '{search_term}' in {file_path}")

@tool
def search_file(search_term: str, file_path: Optional[str] = None) -> None:
    """Searches for `search_term` in a specific file."""
    if not file_path:
        return "Error: No file path provided"
    
    try:
        # Handle file path similarly to open_file
        if os.path.isabs(file_path):
            abs_path = file_path
        else:
            abs_path = os.path.abspath(file_path)
            if not os.path.exists(abs_path):
                workspace = os.getenv("WORKSPACE_ROOT", os.getcwd())
                abs_path = os.path.join(workspace, file_path)
        
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
        
        if search_term in content:
            print(f"Found '{search_term}' in {file_path}")
        else:
            print(f"'{search_term}' not found in {file_path}")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
    except Exception as e:
        print(f"Error reading file: {e}")

@tool
def find_file(file_name: str, dir_path: str = './') -> None:
    """Finds all files with the given name in the specified directory."""
    matches = []
    for root, _, files in os.walk(dir_path):
        if file_name in files:
            matches.append(os.path.join(root, file_name))
    
    if matches:
        print(f"Found {file_name} in:")
        for match in matches:
            print(match)
    else:
        print(f"File '{file_name}' not found in {dir_path}.")

@tool
def list_files(dir_path: str = './') -> None:
    """Lists all files in the given directory."""
    try:
        files = os.listdir(dir_path)
        print(f"Files in '{dir_path}':")
        for file in files:
            print(file)
    except FileNotFoundError:
        print(f"Error: Directory '{dir_path}' not found.")

@tool
def get_relevant_files(problem_statement: str, repo_path: str = None) -> str:
    """
    Retrieves a list of relevant files to edit based on the problem statement and repository structure.
    :param problem_statement: str, The GitHub problem description.
    :param repo_path: str, The path to the repository. If None, the current working directory is used.
    :return: str, The list of relevant files.
    """
    obtain_relevant_files_prompt = """
    Please look through the following GitHub problem description and Repository structure and provide a list of files that one would need to edit to fix the problem.

    ### GitHub Problem Description ###
    {problem_statement}

    ###

    ### Repository Structure ###
    {structure}

    ###

    Please only provide the full path and return at most 5 files.
    The returned files should be separated by new lines ordered by most to least important and wrapped with ```
    For example:
    ```
    file1.py
    file2.py
    ```
    """

    repo_path = repo_path or os.getcwd()
    structure = get_repo_tree(repo_path)
    prompt = obtain_relevant_files_prompt.format(problem_statement=problem_statement, structure=structure)
    message = [
        ("human", prompt)
    ]
    llm1 = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    response = llm1.invoke(input=message)
    return response.content
