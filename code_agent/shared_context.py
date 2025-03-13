"""Module for storing shared context between different parts of the application."""

from typing import Dict, Optional

# Global structure variable that will be set by run_agent
structure: Optional[Dict] = None

def set_structure(new_structure: Dict) -> None:
    """Set the global structure variable."""
    global structure
    structure = new_structure

def get_structure() -> Optional[Dict]:
    """Get the current structure."""
    return structure