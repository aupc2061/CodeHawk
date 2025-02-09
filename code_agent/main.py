import os
from typing import Optional
from imports import *
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph
from code_agent.config import GOOGLE_API_KEY, GROQ_API_KEY
from code_agent.core import (
    AgentState, create_agent, create_agent_node, 
    feedback as user_feedback, route_feedback
)
from code_agent.routing import (
    router, code_analyzer_router, code_editor_router
)
from code_agent.tools import *
from code_agent.config import (
    PLANNER_PROMPT, EDITING_AGENT_PROMPT, CODE_ANALYZER_PROMPT
)

def create_structure(directory_path):
    """Create the structure of the repository directory by parsing Python files.
    :param directory_path: Path to the repository directory.
    :return: A dictionary representing the structure.
    """
    structure = {}

    for root, _, files in os.walk(directory_path):
        repo_name = os.path.basename(directory_path)
        # print("repo name", repo_name)
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

structure = create_structure(os.getcwd())

@tool
def get_class_info(relative_file_path, class_name):
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
def get_function_info(relative_file_path, function_name):
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

def format_class_and_function_info(info):
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
            # result.append("\n")
    return "\n".join(result)

@tool
def get_class_and_function_info(relative_file_path : str):
    """
    Retrieves class and function info from the repo map for a given relative file path.
    
    :param relative_file_path: str, The relative file path to look up in the structure
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


def build_agent_graph(model: str = "claude", temperature: float = 0):
    """Build and return the agent graph with specified model"""
    
    # Initialize the LLM
    if model == "claude":
        llm = ChatAnthropic(
            model='claude-3-sonnet-20240229',
            temperature=temperature
        )
    else:
        raise ValueError(f"Unsupported model: {model}")

    # Create tool nodes
    planner_tools = [get_repo_tree]  
    editor_tools = [get_repo_tree, list_files, open_file, edit_file, find_file, search_file, create_file, search_dir]
    analysis_tools = [get_class_and_function_info, get_repo_tree, get_relevant_files, open_file, get_class_info, get_function_info]

    planner_tool_node = ToolNode(planner_tools)
    editor_tool_node = ToolNode(editor_tools)
    analysis_tool_node = ToolNode(analysis_tools)

    # Create agents
    planner_agent = create_agent(PLANNER_PROMPT, planner_tools, llm)
    editor_agent = create_agent(EDITING_AGENT_PROMPT, editor_tools, llm) 
    analysis_agent = create_agent(CODE_ANALYZER_PROMPT, analysis_tools, llm)

    # Create agent nodes
    planner_node = create_agent_node(planner_agent, "planner")
    editor_node = create_agent_node(editor_agent, "code_editor")
    analysis_node = create_agent_node(analysis_agent, "code_analysis")

    # Build the graph
    graph_builder = StateGraph(AgentState)

    # Add nodes
    graph_builder.add_node("planner", planner_node)
    graph_builder.add_node("code_editor", editor_node)
    graph_builder.add_node("code_analysis", analysis_node)
    graph_builder.add_node("HIL", user_feedback)
    graph_builder.add_node("planner_tool", planner_tool_node)
    graph_builder.add_node("code_edit_tool", editor_tool_node)
    graph_builder.add_node("code_analysis_tool", analysis_tool_node)

    # Add edges
    graph_builder.add_edge("START", "planner")

    # Add conditional edges
    graph_builder.add_conditional_edges(
        "planner",
        router,
        {
            "planner_tool": "planner_tool",
            "__end__": END,
            "continue": "planner",
            "analyze_code": "code_analysis", 
            "edit_file": "code_editor",
            "ask_user": "HIL"
        }
    )

    graph_builder.add_conditional_edges(
        "HIL",
        route_feedback,
        {
            "code_editor": "code_editor",
            "planner": "planner"
        }
    )

    graph_builder.add_conditional_edges(
        "code_analysis",
        code_analyzer_router,
        {
            "continue": "code_analysis",
            "done": "planner",
            "edit_file": "code_editor",  
            "code_analysis_tool": "code_analysis_tool",
        }
    )

    graph_builder.add_conditional_edges(
        "code_editor",
        code_editor_router,
        {
            "continue": "code_editor",
            "done": "planner",
            "code_edit_tool": "code_edit_tool",
        }
    )

    def route_sender(state: AgentState):
        return state["sender"] if state["sender"] in {"planner", "code_editor", "code_analysis"} else "planner"

    for tool_node in ["planner_tool", "code_edit_tool", "code_analysis_tool"]:
        graph_builder.add_conditional_edges(
            tool_node,
            route_sender,
            {
                "planner": "planner",
                "code_editor": "code_editor",
                "code_analysis": "code_analysis",
            }
        )

    return graph_builder.compile()


def run_agent(
    question: str,
    model: str = "claude",
    temperature: float = 0,
    log_file: Optional[str] = None
):
    """Run the code agent on a given question"""
    
    graph = build_agent_graph(model, temperature)
    
    # Initialize state
    state = {
        "messages": [HumanMessage(content=question)],
        "sender": "user"
    }
    
    # Stream results
    for step in graph.stream(state):
        if log_file:
            with open(log_file, 'a') as f:
                f.write(f"{step}\n---\n")
        
        for key, value in step.items():
            print(f"Output from node '{key}':")
            print("---")
            print(value)
            print("\n---\n")