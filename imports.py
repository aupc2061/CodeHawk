import os
import shutil
import subprocess
import operator
import traceback
import typing as t
import json
import ast
import re
import time
import pprint
import dotenv
from typing import Annotated, Literal, Sequence, Optional
from typing_extensions import TypedDict
import warnings

# LangChain and related imports
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.tools import tool
from langchain_core.tools import tool
from langchain_core.tools.simple import Tool
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain.schema.language_model import BaseLanguageModel
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticToolsParser
from pydantic import BaseModel, Field

# Notebook-specific imports
from pathlib import Path
from IPython.display import Image, display
from google.api_core.exceptions import ResourceExhausted