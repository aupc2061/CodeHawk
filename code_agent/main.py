import os
from time import sleep
from rich.console import Console
from rich.text import Text
from typing import Optional
from imports import *
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph
from code_agent.config import GOOGLE_API_KEY, GROQ_API_KEY, ANTHROPIC_API_KEY
from code_agent.core import (
    create_agent, create_agent_node, 
    feedback as user_feedback, route_feedback
)
from code_agent.routing import (
    router, code_analyzer_router, code_editor_router
)
from code_agent.tools import *
from code_agent.structure import create_structure
from code_agent.shared_context import set_structure
from IPython.display import Image, display

from code_agent.config import (
    PLANNER_PROMPT, EDITING_AGENT_PROMPT, CODE_ANALYZER_PROMPT
)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    sender: str

def build_agent_graph(model: str = "claude", temperature: float = 0):
    """Build and return the agent graph with specified model"""
    
    # Initialize the LLM
    if model == "claude":
        llm = ChatAnthropic(
            model='claude-3-sonnet-20240229',
            temperature=temperature,
            api_key=ANTHROPIC_API_KEY
        )
    elif model == "gemini":
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001", temperature=0, api_key=GOOGLE_API_KEY)
    elif model == 'llama':
        llm = ChatOpenAI(model='llama3-70b-8192',  base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY, temperature=temperature)
    else:
        raise ValueError(f"Unsupported model: {model}")

    # Create tool nodes with bound structure
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
    graph_builder.add_edge(START, "planner")

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

console = Console()
COLORS = {
    "planner": "bold cyan",
    "code_editor": "bold green",
    "code_analysis": "bold magenta",
    "HIL": "bold yellow"
}


def run_agent(
    question: str,
    model: str = "claude",
    temperature: float = 0,
    log_file: Optional[str] = None,
    workspace_dir: Optional[str] = None
):
    """Run the code agent on a given question
    
    Args:
        question: The question or task for the agent
        model: LLM model to use ("claude", "gemini", or "groq")
        temperature: Temperature parameter for the LLM
        log_file: Optional path to log file
        workspace_dir: Optional path to workspace directory. Defaults to current directory
    """
    
    # Use provided workspace dir or current directory
    workspace_dir = workspace_dir or os.getcwd()
    
    # Change current working directory to workspace directory
    original_cwd = os.getcwd()
    os.chdir(workspace_dir)
    
    try:
        # Create structure for the workspace directory
        structure = create_structure(workspace_dir)
        # Set the structure in shared context
        set_structure(structure)
        
        # Build graph with structure
        graph = build_agent_graph(model, temperature)
        
        # Initialize state
        state = {
            "messages": [HumanMessage(content=question)],
            "sender": "user"
        }

        for step in graph.stream(state):
            if log_file:
                with open(log_file, 'a') as f:
                    f.write(f"{step}\n---\n")
            for key, value in step.items():
                # if key in COLORS:  # Check if the key is in the color mapping
                #     if isinstance(value, dict) and "messages" in value:
                #         for message in value["messages"]:
                #             if isinstance(message, AIMessage):
                #                 content = message.content  # Extract only the message text
                #                 console.print(f"\n[{key.upper()}]: {content}\n", style=COLORS[key])
                pprint.pprint(f"Output from node '{key}':")
                pprint.pprint("---")
                pprint.pprint(value, indent=2, width=80, depth=None)
            pprint.pprint("\n---\n")
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
