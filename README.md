# CodeHawk

An intelligent multi-agent system powered by LangChain and LangGraph that provides advanced code analysis, modification, and maintenance capabilities through natural language interactions.

## Features

- **Multi-Agent Architecture**: 
  - Planner Agent: Orchestrates tasks and makes high-level decisions
  - Code Analysis Agent: Performs deep code understanding with AST parsing
  - Code Editor Agent: Handles precise code modifications with context awareness
  - Human-in-the-Loop Validation: Interactive approval system for code changes

- **Various LLM Integration**:
  - Claude-3 Sonnet (Primary model for precise code understanding)
  - Gemini 2.0 Flash (Fast and efficient for simpler tasks)
  - LLaMA 70B via Groq (Open-source alternative)

- **Comprehensive Tool Suite**:
  - Code Analysis: AST parsing, function/class analysis, docstring extraction
  - Repository Navigation: Smart file search, tree generation, context-aware editing
  - Interactive CLI: Rich text formatting, progress tracking, and intuitive workflow

## Technical Implementation

### Architecture 

The system uses LangGraph's directed graph architecture to implement a sophisticated multi-agent workflow:

1. **Planner Agent**:
   - Task decomposition and strategy planning
   - Intelligent routing between analysis and editing agents
   - Progress monitoring and completion verification

2. **Code Analysis Agent**:
   - Deep code structure analysis using Python's AST
   - Smart relevancy detection for files and code segments
   - Context-aware code understanding

3. **Code Editor Agent**:
   - Precise code modifications with indentation preservation
   - Smart file handling with encoding detection
   - Validation of changes through error checking

### Key Components

- **State Management**: Uses TypedDict for maintaining conversation and agent state
- **Tool System**: Implements custom tools for code analysis and manipulation using Python's AST
- **Routing Logic**: Dynamic message routing between agents based on intent detection
- **Human-in-the-Loop**: Interactive feedback system for code change approval

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
│   ├── shared_context.py
│   ├── tools.py
|   ├── structure.py
│   └── tree_context.py
├── imports.py
├── requirements.txt
├── setup.py
├── test.py
└── README.md

```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/aupc2061/CodeHawk
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
pip install -r requirements.txt
pip install -e .
```

4. Configure environment:
Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
```

## Usage

### Interactive Mode (Recommended)
```bash
python test.py
```
This launches an interactive session with:
- Rich text interface
- Model selection menu
- Workspace management
- Progress tracking

### Command Line Mode
```bash
python test.py -q "Your request" -m "model_name" -w "workspace_path"
```
Arguments:
- `-q/--question`: Your natural language request
- `-m/--model`: Model choice (claude/gemini/llama)
- `-w/--workspace`: Target workspace directory

## Dependencies

Key dependencies include:
- `langgraph>=0.0.15`: Multi-agent graph architecture
- `langchain-anthropic>=0.1.1`: Claude integration
- `langchain-core>=0.1.15`: Core functionality
- `rich`: Terminal formatting and UI
- See `requirements.txt` for complete list

## Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Submit a pull request


