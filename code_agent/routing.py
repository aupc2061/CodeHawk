from typing import Literal
from langchain_core.messages import AIMessage
from langgraph.graph import END

def router(state) -> Literal[
        "code_edit_tool",
        "code_analysis_tool",
        "__end__",
        "continue",
        "analyze_code",
        "edit_file",
        "planner_tool",
        "ask_user",
    ]:
    messages = state["messages"]
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            last_ai_message = message
            break
    else:
        last_ai_message = messages[-1]

    if last_ai_message.tool_calls:
        return "planner_tool"
    if "ANALYZE CODE" in last_ai_message.content:
        return "analyze_code"
    if "ASK USER" in last_ai_message.content:
        return "ask_user"
    if "EDIT FILE" in last_ai_message.content:
        return "edit_file"
    if "PATCH COMPLETED" in last_ai_message.content:
        return "__end__"
    return "continue"

def code_analyzer_router(state):
    messages = state["messages"]
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            last_ai_message = message
            break
    else:
        last_ai_message = messages[-1]

    if last_ai_message.tool_calls:
        return "code_analysis_tool"
    if "ANALYSIS COMPLETE" in last_ai_message.content:
        return "done"
    if "EDIT FILE" in last_ai_message.content:
        return "edit_file"
    return "continue"

def code_editor_router(state):
    messages = state["messages"]
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            last_ai_message = message
            break
    else:
        last_ai_message = messages[-1]

    if last_ai_message.tool_calls:
        return "code_edit_tool"
    if "FILE OPENED" in last_ai_message.content:
        return "continue"
    if "EDITING COMPLETED" in last_ai_message.content:
        return "done"
    return "continue"