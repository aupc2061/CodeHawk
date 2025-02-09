from collections import defaultdict, namedtuple, Counter
import math
import networkx as nx
from typing import List, Set, Dict, Tuple, Optional
from pathlib import Path
from pygments.token import Token
from pygments.lexers import guess_lexer_for_filename
from grep_ast import TreeContext, filename_to_lang
from tree_sitter_languages import get_language, get_parser
from code_agent.tree_context import to_tree
from code_agent.code_walker import filter_important_files, is_important

import os

from .progress import Spinner

Tag = namedtuple("Tag", "rel_fname fname line name kind")

def get_scm_fname(lang):
    # Load the tags queries
    try:
        # base_path = Path(__file__).parent
        base_path = Path(os.getcwd())
        return base_path.joinpath("queries", f"tree-sitter-{lang}-tags.scm")
    except KeyError:
        return

def get_tags_raw(fname, rel_fname):
        lang = filename_to_lang(fname)
        if not lang:
            return

        try:
            language = get_language(lang)
            parser = get_parser(lang)
        except Exception as err:
            print(f"Skipping file {fname}: {err}")
            return

        query_scm = get_scm_fname(lang)
        if not query_scm.exists():
            return
        query_scm = query_scm.read_text()

        # Read source code
        with open(fname, 'r', encoding="utf-8") as f:
            code = f.read()
        if not code:
            return
        tree = parser.parse(bytes(code, "utf-8"))

        # Run the tags queries
        query = language.query(query_scm)
        captures = query.captures(tree.root_node)

        captures = list(captures)

        saw = set()
        for node, tag in captures:
            if tag.startswith("name.definition."):
                kind = "def"
            elif tag.startswith("name.reference."):
                kind = "ref"
            else:
                continue

            saw.add(kind)

            result = Tag(
                rel_fname=rel_fname,
                fname=fname,
                name=node.text.decode("utf-8"),
                kind=kind,
                line=node.start_point[0],
            )

            yield result

        if "ref" in saw:
            return
        if "def" not in saw:
            return

        # We saw defs, without any refs
        # Some tags files only provide defs (cpp, for example)
        # Use pygments to backfill refs

        try:
            lexer = guess_lexer_for_filename(fname, code)
        except Exception:  # On Windows, bad ref to time.clock which is deprecated?
            # self.io.tool_error(f"Error lexing {fname}")
            print("Error lexing {fname}")
            return

        tokens = list(lexer.get_tokens(code))
        tokens = [token[1] for token in tokens if token[0] in Token.Name]

        for token in tokens:
            yield Tag(
                rel_fname=rel_fname,
                fname=fname,
                name=token,
                kind="ref",
                line=-1,
            )

def get_tags(fname, rel_fname):
        """Get tags for a single file"""
        data = list(get_tags_raw(fname, rel_fname))

        return data

def get_rel_fname(fname: str, root: str = None) -> str:
    """Get relative path from root directory."""
    try:
        return os.path.relpath(fname, root) if root else fname
    except ValueError:
        return fname

def get_ranked_tags(
    chat_fnames: List[str],
    other_fnames: List[str],
    mentioned_fnames: Set[str],
    mentioned_idents: Set[str],
    progress: Optional[callable] = None
) -> List[Tag]:
    """
    Rank tags based on their importance in the codebase.
    
    Args:
        chat_fnames: List of filenames currently being discussed
        other_fnames: List of other relevant filenames
        mentioned_fnames: Set of filenames mentioned in the conversation
        mentioned_idents: Set of identifiers mentioned in the conversation
        progress: Optional callback for progress updates
    
    Returns:
        List of ranked tags
    """
    defines = defaultdict(set)
    references = defaultdict(list)
    definitions = defaultdict(set)
    personalization = dict()

    fnames = set(chat_fnames).union(set(other_fnames))
    chat_rel_fnames = set()
    fnames = sorted(fnames)
    
    personalize = 100 / len(fnames)

    for fname in fnames:
        if progress:
            progress()

        try:
            file_ok = Path(fname).is_file()
        except OSError:
            continue

        rel_fname = get_rel_fname(fname)

        if fname in chat_fnames:
            personalization[rel_fname] = personalize
            chat_rel_fnames.add(rel_fname)

        if rel_fname in mentioned_fnames:
            personalization[rel_fname] = personalize

        tags = list(get_tags(fname, rel_fname))
        if tags is None:
            continue

        for tag in tags:
            if tag.kind == "def":
                defines[tag.name].add(rel_fname)
                key = (rel_fname, tag.name)
                definitions[key].add(tag)
            elif tag.kind == "ref":
                references[tag.name].append(rel_fname)

    if not references:
        references = dict((k, list(v)) for k, v in defines.items())

    idents = set(defines.keys()).intersection(set(references.keys()))

    G = nx.MultiDiGraph()

    for ident in idents:
        if progress:
            progress()

        definers = defines[ident]
        mul = 10 if ident in mentioned_idents else (0.1 if ident.startswith("_") else 1)

        for referencer, num_refs in Counter(references[ident]).items():
            for definer in definers:
                num_refs = math.sqrt(num_refs)
                G.add_edge(referencer, definer, weight=mul * num_refs, ident=ident)

    if personalization:
        pers_args = dict(personalization=personalization, dangling=personalization)
    else:
        pers_args = dict()

    try:
        ranked = nx.pagerank(G, weight="weight", **pers_args)
    except ZeroDivisionError:
        try:
            ranked = nx.pagerank(G, weight="weight")
        except ZeroDivisionError:
            return []

    ranked_definitions = defaultdict(float)
    for src in G.nodes:
        if progress:
            progress()

        src_rank = ranked[src]
        total_weight = sum(data["weight"] for _src, _dst, data in G.out_edges(src, data=True))
        
        for _src, dst, data in G.out_edges(src, data=True):
            data["rank"] = src_rank * data["weight"] / total_weight
            ident = data["ident"]
            ranked_definitions[(dst, ident)] += data["rank"]

    ranked_tags = []
    ranked_definitions = sorted(
        ranked_definitions.items(), reverse=True, key=lambda x: (x[1], x[0])
    )

    for (fname, ident), rank in ranked_definitions:
        if fname in chat_rel_fnames:
            continue
        ranked_tags += list(definitions.get((fname, ident), []))

    rel_other_fnames_without_tags = set(get_rel_fname(fname) for fname in other_fnames)
    fnames_already_included = set(rt[0] for rt in ranked_tags)

    top_rank = sorted([(rank, node) for (node, rank) in ranked.items()], reverse=True)
    for rank, fname in top_rank:
        if fname in rel_other_fnames_without_tags:
            rel_other_fnames_without_tags.remove(fname)
        if fname not in fnames_already_included:
            ranked_tags.append((fname,))

    for fname in rel_other_fnames_without_tags:
        ranked_tags.append((fname,))

    return ranked_tags

def token_count(text):
    return len(text.split(" "))

def get_ranked_tags_map_uncached(
        chat_fnames,
        other_fnames=None,
        max_map_tokens=None,
        mentioned_fnames=None,
        mentioned_idents=None,
    ):
        if not other_fnames:
            other_fnames = list()
        if not max_map_tokens:
            max_map_tokens = max_map_tokens
        if not mentioned_fnames:
            mentioned_fnames = set()
        if not mentioned_idents:
            mentioned_idents = set()

        spin = Spinner("Updating repo map")

        ranked_tags = get_ranked_tags(
            chat_fnames,
            other_fnames,
            mentioned_fnames,
            mentioned_idents,
            progress=spin.step,
        )

        other_rel_fnames = sorted(set(get_rel_fname(fname) for fname in other_fnames))
        special_fnames = filter_important_files(other_rel_fnames)
        ranked_tags_fnames = set(tag[0] for tag in ranked_tags)
        special_fnames = [fn for fn in special_fnames if fn not in ranked_tags_fnames]
        special_fnames = [(fn,) for fn in special_fnames]

        ranked_tags = special_fnames + ranked_tags

        spin.step()

        num_tags = len(ranked_tags)
        lower_bound = 0
        upper_bound = num_tags
        best_tree = None
        best_tree_tokens = 0

        chat_rel_fnames = set(get_rel_fname(fname) for fname in chat_fnames)
        tree = to_tree(ranked_tags[:num_tags], chat_rel_fnames)
        num_tokens = token_count(tree)

        if num_tokens > max_map_tokens:
            print(f"Warning: The generated tree exceeds the max_map_tokens limit by {num_tokens - max_map_tokens} tokens.")

        return tree