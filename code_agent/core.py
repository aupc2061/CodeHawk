from typing import Annotated, Literal, Sequence, List, Set, Dict, Optional
from typing_extensions import TypedDict
from langchain.schema.language_model import BaseLanguageModel
from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from code_agent.config import PLANNER_PROMPT, CODE_ANALYZER_PROMPT, EDITING_AGENT_PROMPT
from code_agent.tools import *
from pathlib import Path
import os
import networkx as nx
from collections import Counter
from main import create_structure
from .code_walker import find_src_files, filter_important_files
# from .code_analyzer import parse_python_file, create_structure
from .progress import Spinner
from .repo_mapper import get_ranked_tags, Tag
from .tree_context import to_tree


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    sender: str

def create_agent_node(agent, name):
    def agent_node(state):
        # If last message is AI message, add a placeholder human message
        if isinstance(state["messages"][-1], AIMessage):
            state["messages"].append(HumanMessage(content="Placeholder message"))

        result = agent.invoke(state)

        if not isinstance(result, dict):
            result = {"messages": [result], "sender": name}

        return result

    return agent_node

def create_agent(system_prompt: str, tools: list = None, llm: BaseLanguageModel = None):
    """Create an agent with given prompt and tools"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    if tools and llm:
        return prompt | llm.bind_tools(tools)
    else:
        return prompt | llm

def feedback(state):
    """Gets feedback from the human user on whether to accept the proposed code changes."""
    messages = state["messages"]

    # Find the code content message
    proposed_changes = "No code changes found"
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            import re
            code_match = re.search(r'```(?:python)?\n(.*?)```', message.content, re.DOTALL)
            if code_match:
                proposed_changes = code_match.group(1).strip()
                break
    
    print("\nProposed code changes:")
    print(proposed_changes)
    print("\nDo you approve these changes? (yes/no):")
    
    user_input = input().lower().strip()
    return {
        "messages": [HumanMessage(content=f"User feedback: {user_input}")], 
        "sender": "user"
    }

def route_feedback(state) -> Literal["code_editor", "planner"]:
    """Routes to either code_editor or planner based on user feedback"""
    messages = state["messages"]
    last_message = messages[-1]
    
    if not isinstance(last_message, HumanMessage):
        return "planner"
        
    feedback = last_message.content.lower()
    if "yes" in feedback:
        return "code_editor" 
    else:
        return "planner"

class CodeStructureAnalyzer:
    """Main class for analyzing code structure and generating repository maps."""
    
    def __init__(self, root_path: str, max_map_tokens: int = 1024):
        self.root_path = Path(root_path)
        self.max_map_tokens = max_map_tokens
        
    def analyze_files(self, target_files: List[str]) -> Dict:
        """Analyze specified files and create a structure map."""
        chat_fnames = []
        other_fnames = []
        
        for fname in target_files:
            if Path(fname).is_dir():
                chat_fnames += find_src_files(fname)
            else:
                chat_fnames.append(fname)
                
        return create_structure(self.root_path)
        
    def generate_repo_map(
        self,
        chat_fnames: List[str],
        other_fnames: Optional[List[str]] = None,
        mentioned_fnames: Optional[Set[str]] = None,
        mentioned_idents: Optional[Set[str]] = None
    ) -> str:
        """Generate a repository map showing code structure and relationships."""
        if not other_fnames:
            other_fnames = []
        if not mentioned_fnames:
            mentioned_fnames = set()
        if not mentioned_idents:
            mentioned_idents = set()

        spinner = Spinner("Updating repo map")
        
        ranked_tags = get_ranked_tags(
            chat_fnames,
            other_fnames,
            mentioned_fnames,
            mentioned_idents,
            progress=spinner.step,
        )

        other_rel_fnames = sorted(set(
            os.path.relpath(fname, self.root_path) 
            for fname in other_fnames
        ))
        
        special_fnames = filter_important_files(other_rel_fnames)
        ranked_tags_fnames = set(tag[0] for tag in ranked_tags)
        special_fnames = [fn for fn in special_fnames if fn not in ranked_tags_fnames]
        special_fnames = [(fn,) for fn in special_fnames]

        ranked_tags = special_fnames + ranked_tags
        spinner.step()

        chat_rel_fnames = set(
            os.path.relpath(fname, self.root_path) 
            for fname in chat_fnames
        )
        tree = to_tree(ranked_tags[:len(ranked_tags)], chat_rel_fnames)
        
        spinner.end()
        return tree