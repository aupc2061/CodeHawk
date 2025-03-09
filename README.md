# CodeHawk

An intelligent code agent built with LangChain and LangGraph that can understand, analyze, and modify code through natural language interactions.

## Features

- **Multi-Agent Architecture**: Utilizes specialized agents for planning, code analysis, and code editing
- **Intelligent Code Analysis**: Parses and analyzes Python code to understand classes, functions, and their relationships
- **Interactive Code Editing**: Makes code changes with user approval through a human-in-the-loop feedback system
- **Flexible LLM Support**: Currently supports Claude-3 with extensible architecture for other models
- **Rich Tool Suite**: Includes tools for code parsing, analysis, and manipulation

## Technical Implementation

### Architecture Overview

CodeHawk implements a multi-agent system using LangGraph's directed graph architecture:

1. **Planner Agent**: Coordinates overall task execution and delegates to specialized agents
2. **Code Analysis Agent**: Performs deep code understanding and structure analysis
3. **Code Editor Agent**: Handles code modifications with user approval

### Key Components

- **State Management**: Uses TypedDict for maintaining conversation and agent state
- **Tool System**: Implements custom tools for code analysis and manipulation using Python's AST
- **Routing Logic**: Dynamic message routing between agents based on intent detection
- **Human-in-the-Loop**: Interactive feedback system for code change approval

### LLM Integration

- Primary support for Claude-3 (Anthropic)
- Extensible architecture supporting multiple LLM providers
- Temperature control for deterministic outputs
- Tool-augmented prompting for specialized tasks

## Project Structure

```
├── code_agent/
│   ├── __init__.py
│   ├── codewalker.py
│   ├── config.py
│   ├── core.py
│   ├── main.py
│   ├── progress.py
│   ├── repo_mapper.py
│   ├── routing.py
│   ├── tools.py
│   └── tree_context.py
├── imports.py
├── requirements.txt
├── setup.py
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CodeHawk.git
cd CodeHawk
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Unix/macOS
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
# Install base requirements
pip install -r requirements.txt

# Install the package in editable mode
pip install -e .
```

4. Set up environment variables:
Create a `.env` file in the root directory with your API keys:
```
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key

```

## Usage

```python
from code_agent.main import run_agent

# Run the code agent with a natural language question/request
run_agent(
    question="Please analyze the structure of this codebase",
    model="claude",  # Currently supports "claude"
    temperature=0    # Lower values for more deterministic responses
)
```

## Tools

The agent comes with several built-in tools:

### Code Analysis
- AST-based Python code parsing
- Docstring extraction
- Function signature analysis
- Class and method detection

### File Operations
- Smart file editing with context awareness
- Directory traversal and search
- File content manipulation

### Workspace Management
- Repository structure analysis
- File tree generation
- Code search capabilities

## Dependencies

Key dependencies include:
- `langgraph`: For building the multi-agent system
- `langchain-anthropic`: Claude LLM integration
- `langchain-core`: Core functionality
- `python-dotenv`: Environment management
- `tiktoken`: Token counting
- See `requirements.txt` for full list

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Development

### Setting Up Development Environment
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: 
   - Windows: `venv\Scripts\activate`
   - Unix: `source venv/bin/activate`
4. Install dependencies: `pip install -e .`

### Running Tests
```bash
python -m pytest tests/
