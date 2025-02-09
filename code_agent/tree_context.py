from typing import Optional, Set, List, Dict
from pathlib import Path
from collections import defaultdict, namedtuple
import ast
import os

Tag = namedtuple("Tag", "rel_fname fname line name kind")


class TreeContext:
    """Handles code tree analysis and context management."""
    def __init__(
        self,
        rel_fname: str,
        code: str,
        color: bool = False,
        line_number: bool = False,
        child_context: bool = False,
        last_line: bool = False,
        margin: int = 0,
        mark_lois: bool = False,
        loi_pad: int = 0,
        show_top_of_file_parent_scope: bool = False,
    ):
        self.rel_fname = rel_fname
        self.code = code
        self.color = color
        self.line_number = line_number
        self.child_context = child_context
        self.last_line = last_line
        self.margin = margin
        self.mark_lois = mark_lois
        self.loi_pad = loi_pad
        self.show_top_of_file_parent_scope = show_top_of_file_parent_scope
        self.lines_of_interest = set()
        self._parsed = None

    def add_lines_of_interest(self, lines: List[int]) -> None:
        """Add lines to be highlighted in the code."""
        if not lines:
            return
        self.lines_of_interest.update(lines)

    def add_context(self) -> None:
        """Add context around lines of interest."""
        if not self.lines_of_interest:
            return

        expanded_lines = set()
        for line in self.lines_of_interest:
            start = max(0, line - self.loi_pad)
            end = line + self.loi_pad + 1
            expanded_lines.update(range(start, end))
        self.lines_of_interest = expanded_lines

    def format(self) -> str:
        """Format the code with proper indentation and highlighting."""
        lines = self.code.splitlines()
        output = []
        
        for i, line in enumerate(lines):
            if not self.lines_of_interest or i in self.lines_of_interest:
                if self.line_number:
                    line_num = f"{i+1:4d} "
                else:
                    line_num = ""
                    
                margin = " " * self.margin
                marked = "→ " if self.mark_lois and i in self.lines_of_interest else "  "
                output.append(f"{margin}{marked}{line_num}{line}")

        return "\n".join(output)

def to_tree(tags: List[tuple], chat_rel_fnames: Set[str]) -> str:
    """Convert tags to a tree representation of the code structure."""
    if not tags:
        return ""

    cur_fname = None
    cur_abs_fname = None
    lois = None
    output = ""
    dummy_tag = Tag(rel_fname="dummy", fname="dummy", line=999999, name="dummy", kind="dummy")
    
    for tag in sorted(tags) + [dummy_tag]:
        this_rel_fname = tag[0]

        if this_rel_fname != cur_fname:
            if lois is not None:
                output += "\n"
                output += cur_fname + ":\n"
                output += render_tree(cur_abs_fname, cur_fname, lois)
                lois = None
            elif cur_fname:
                output += "\n" + cur_fname + "\n"
            if hasattr(tag, '_fields'):  # Check if it's a Tag namedtuple
                lois = []
                cur_abs_fname = tag.fname
            cur_fname = this_rel_fname

        if lois is not None:
            lois.append(tag.line)

    # Truncate long lines
    output = "\n".join([line[:100] for line in output.splitlines()]) + "\n"
    return output

def render_tree(abs_fname: str, rel_fname: str, lois: List[int]) -> str:
    """Render a tree view of the code file highlighting specific lines."""
    try:
        with open(abs_fname, 'r', encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        return f"Error reading file {abs_fname}: {str(e)}"

    if not code.endswith("\n"):
        code += "\n"

    context = TreeContext(
        rel_fname,
        code,
        color=False,
        line_number=False,
        child_context=False,
        last_line=False,
        margin=0,
        mark_lois=False,
        loi_pad=0,
        show_top_of_file_parent_scope=False,
    )
    
    context.lines_of_interest = set()
    context.add_lines_of_interest(lois)
    context.add_context()
    return context.format()