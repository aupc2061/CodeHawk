"""Functions for creating and managing repository structure."""
import os
import ast
from typing import Dict, Optional

def get_docstring(node):
    """Extract docstring from AST node if it exists."""
    if (node.body and isinstance(node.body[0], ast.Expr) 
        and isinstance(node.body[0].value, ast.Str)):
        return node.body[0].value.s
    return None

def get_function_signature(node):
    """Extract function signature from AST node."""
    args_list = []
    
    for arg in node.args.posonlyargs:
        args_list.append(arg.arg)
        
    for arg in node.args.args:
        args_list.append(arg.arg)
        
    defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + node.args.defaults
    for arg, default in zip(node.args.args, defaults):
        if default:
            try:
                default_value = ast.literal_eval(default)
                args_list.append(f"{arg.arg}={default_value}")
            except:
                args_list.append(f"{arg.arg}=...")

    if node.args.vararg:
        args_list.append(f"*{node.args.vararg.arg}")

    for kwarg in node.args.kwonlyargs:
        args_list.append(kwarg.arg)

    if node.args.kwarg:
        args_list.append(f"**{node.args.kwarg.arg}")
        
    docstring = get_docstring(node)
    signature = f"{node.name}({', '.join(args_list)})"
    
    if docstring:
        signature += f'\n    """{docstring}"""'
    
    return signature


def parse_python_file(file_path, file_content=None):
    """Parse a Python file to extract class and function definitions with their line numbers."""
    if file_content is None:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                file_content = file.read()
                parsed_data = ast.parse(file_content)
        except Exception as e:
            print(f"Error in file {file_path}: {e}")
            return [], [], ""
    else:
        try:
            parsed_data = ast.parse(file_content)
        except Exception as e:
            print(f"Error in file {file_path}: {e}")
            return [], [], ""

    class_info = []
    function_names = []
    class_methods = set()

    for node in ast.walk(parsed_data):
        if isinstance(node, ast.ClassDef):
            methods = []
            for n in node.body:
                if isinstance(n, ast.FunctionDef):
                    methods.append(
                        {
                            "name": n.name,
                            "signature": "def " + get_function_signature(n),
                            "start_line": n.lineno,
                            "end_line": n.end_lineno,
                            "text": "\n".join(file_content.splitlines()[
                                n.lineno - 1 : n.end_lineno
                            ]),
                        }
                    )
                    class_methods.add(n.name)
            class_info.append(
                {
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                    "text": "\n".join(file_content.splitlines()[
                        node.lineno - 1 : node.end_lineno
                    ]),
                    "methods": methods
                }
            )
        elif isinstance(node, ast.FunctionDef):
            if node.name not in class_methods:
                function_names.append(
                    {
                        "name": node.name,
                        "signature": get_function_signature(node),
                        "start_line": node.lineno,
                        "end_line": node.end_lineno,
                        "text": "\n".join(file_content.splitlines()[
                            node.lineno - 1 : node.end_lineno
                        ]),
                    }
                )

    return class_info, function_names, file_content.splitlines()

def create_structure(directory_path: str) -> Dict:
    """Create the structure of the repository directory by parsing Python files.
    :param directory_path: Path to the repository directory.
    :return: A dictionary representing the structure.
    """
    structure = {}

    for root, _, files in os.walk(directory_path):
        repo_name = os.path.basename(directory_path)
        relative_root = os.path.relpath(root, directory_path)
        if relative_root == ".":
            relative_root = repo_name
        curr_struct = structure
        for part in relative_root.split(os.sep):
            if part not in curr_struct:
                curr_struct[part] = {}
            curr_struct = curr_struct[part]
        for file_name in files:
            if file_name.endswith(".py"):
                file_path = os.path.join(root, file_name)
                class_info, function_names, file_lines = parse_python_file(file_path)
                curr_struct[file_name] = {
                    "classes": class_info,
                    "functions": function_names,
                    "text": file_lines,
                }
            else:
                curr_struct[file_name] = {}

    return structure