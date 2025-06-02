import json
from openai import OpenAI
import os
import ast
from .prompts import PROMPT_TEMPLATES
# from prompts2 import PROMPT_TEMPLATES

def find_merge_candidates(nodes, parent_node=None):
    """
    Identifies nodes where only the minimum count leaf node among siblings is a merge candidate
    or a non-leaf node with only one child and minimum count among siblings.

    Parameters:
        nodes (dict): A dictionary of nodes to check for merge candidates.
        parent_node (dict): Optional. Parent node for isolated single nodes.

    Returns:
        list: A list of merge candidate nodes, each as a dictionary with details.
    """
    candidates = []
    leaf_nodes = []
    single_child_nodes = []

    # Collect leaf nodes and nodes with a single child
    for code, node in nodes.items():
        count = node.get("count", float("inf"))
        children = node.get("children", {})

        if not children:  # Leaf node
            leaf_nodes.append({
                "code": code,
                "label": node.get("label", "No Label"),
                "count": count,
                "threshold": node.get("threshold", None),
                "is_leaf": True
            })
        elif len(children) == 1:  # Node with only one child
            single_child_nodes.append({
                "code": code,
                "label": node.get("label", "No Label"),
                "count": count,
                "threshold": node.get("threshold", None),
                "is_leaf": False
            })

    # Find the leaf node with the minimum count among leaves
    if leaf_nodes:
        min_leaf = min(leaf_nodes, key=lambda x: x["count"])
        candidates.append(min_leaf)

    # Check nodes with a single child if they are minimum among siblings
    for single_child_node in single_child_nodes:
        sibling_counts = [
            sibling.get("count", float("inf"))
            for sibling_code, sibling in nodes.items()
            if sibling_code != single_child_node["code"]
        ]

        # Compare the node with siblings 
        if sibling_counts:
            if single_child_node["count"] < min(sibling_counts):
                candidates.append(single_child_node)
        else:
            print("no sibling for merge.")

    return candidates




def find_node_by_key(data, key, parent_code=None):
    """
    Recursively searches for a node by key within the data, considering a specified parent code.
    
    Parameters:
        data (dict): The hierarchical JSON data, expected to be a dictionary.
        key (str): The unique key to search for.
        parent_code (str): Optional. The key of the expected parent node.
    
    Returns:
        dict: The found node if located, otherwise None.
    """
    # Iterate over each item in the dictionary
    for node_key, node in data.items():
        # Check if this is the node we're looking for
        if node_key == key and (parent_code is None or node.get("parent_code") == parent_code):
            return node  # Found node
        elif "children" in node:
            # If a specific parent_code is provided, dive directly to that branch
            if parent_code and node_key == parent_code:
                # Search within the specific parent's children
                for child_key, child_node in node["children"].items():
                    if child_key == key:
                        return child_node
                    # Recursively search in deeper levels of this branch
                    found_node = find_node_by_key(node["children"], key, parent_code)
                    if found_node:
                        return found_node
            # Otherwise, search recursively in all children nodes
            found_node = find_node_by_key(node["children"], key, parent_code)
            if found_node:
                return found_node

    return None  # Node not found


def merge_with_parent(candidate, merge_candidates, data, is_top_level=False):
    """
    Merges a candidate node with its parent node and updates all relevant keys and references.

    Parameters:
        candidate (dict): The node to merge.
        merge_candidates (list): List of merge candidates.
        data (dict): The hierarchical JSON data.
        is_top_level (bool): Whether the candidate is at the top level of the hierarchy.

    Returns:
        list: Updated merge_candidates list.
    """
    candidate_code = candidate.get("code")
    candidate_node = find_node_by_key(data, candidate_code)

    if candidate_node is None:
        print(f"Error: Node with code {candidate_code} not found.")
        return merge_candidates

    # Skip merging for top-level nodes
    if is_top_level:
        print(f"Skipping merge for top-level node: {candidate_code}")
        merge_candidates = [mc for mc in merge_candidates if mc["code"] != candidate_code]
        return merge_candidates

    parent_code = candidate_node.get("parent_code")
    parent_node = find_node_by_key(data, parent_code)

    if parent_node is None:
        print(f"Error: Parent code for node {candidate_code} is missing.")
        return merge_candidates

    # Update parent's key
    grand_parent_code = parent_node.get("parent_code")
    grand_parent_node = find_node_by_key(data, grand_parent_code) if grand_parent_code else None

    merged_key = f"{parent_code}_{candidate_code}"
    merged_label = parent_node.get("label")
    merged_children = parent_node.get("children", {})
    merged_count = parent_node.get("count", 0) 
    merged_threshold = max(parent_node.get("threshold", 0), candidate_node.get("threshold", 0))

    merged_node = {
        "label": merged_label,
        "children": merged_children,
        "count": merged_count,
        "threshold": merged_threshold,
        "parent_code": grand_parent_code,
    }

    # Update `parent_code` for each child in the merged node
    for child_code, child_node in merged_node["children"].items():
        child_node["parent_code"] = merged_key

    # Update the grandparent's children with the new merged node key
    if grand_parent_node:
        grand_parent_node["children"][merged_key] = merged_node
        del grand_parent_node["children"][parent_code]
    else:
        # If no grandparent, it means parent is at the top level
        data[merged_key] = merged_node
        del data[parent_code]

    # Remove the candidate node
    del parent_node["children"][candidate_code]

    # Update the merge_candidates list
    merge_candidates = [mc for mc in merge_candidates if mc["code"] != candidate_code]

    print(f"Merged {candidate_code} into {parent_code}, new key: {merged_key}")

    return merge_candidates


def merge_single_child_nodes(data, parent_node=None, is_top_level=False):
    """
    Merges nodes that have no siblings with their parent, except for top-level nodes.

    Parameters:
        data (dict): The hierarchical JSON data.
        parent_node (dict): Optional. The parent node for the current level.
        is_top_level (bool): Whether the current level is the top level.

    Returns:
        None. The data is updated in place.
    """
    nodes = parent_node["children"] if parent_node else data

    # Iterate over a copy of the keys to safely modify the dictionary
    for code in list(nodes.keys()):
        node = nodes[code]
        children = node.get("children", {})

        # Skip merging for top-level nodes but process their children
        if is_top_level:
            if children:
                merge_single_child_nodes(data, parent_node=node, is_top_level=False)
            continue

        # If the node has only one child, call merge_with_parent
        if len(children) == 1:
            child_code, child_node = list(children.items())[0]
            print(f"Identified single child {child_code} for merging into {code}")

            # Construct candidate node for merging
            candidate = {
                "code": child_code,
                "label": child_node.get("label"),
                "count": child_node.get("count", 0),
                "parent_code": code,
                "threshold": child_node.get("threshold"),
                "children": child_node.get("children", {}),
            }

            # Call merge_with_parent
            merge_with_parent(candidate, [], data)

        # Recursively check deeper levels
        elif children:
            merge_single_child_nodes(data, parent_node=node, is_top_level=False)



def process_level(whole_data, nodes, parent_label=None, is_top_level=True, parent_node=None, prompt_template=None):
    merge_candidates = find_merge_candidates(nodes, parent_node=parent_node)
    

    i = 0
    while merge_candidates and isinstance(merge_candidates, list) and i < len(merge_candidates):
        candidate = merge_candidates[i]
        merge_candidates = merge_with_parent(candidate, merge_candidates, whole_data, is_top_level)

    # Recursively process child nodes
    for code in list(nodes.keys()):
        node = nodes[code]
        children = node.get("children", {})
        if children:
            process_level(whole_data, children, parent_label=node.get("label"), is_top_level=False, parent_node=node, prompt_template=prompt_template)


if __name__ == "__main__":
    import json
    # Load the JSON file with thresholds
    with open('output/cpc/abstract_cpc12/cpc_abstract_round1_iter3_updated.json', 'r') as file:
        data = json.load(file)
    whole_data = data

    # Use the prompt template from prompts.py
    prompt_template = PROMPT_TEMPLATES["merge_decision"]

    # Start processing from the top level
    process_level(whole_data, data, is_top_level=True, prompt_template=prompt_template)

    # Merge nodes with no siblings at the end, excluding top-level nodes
    merge_single_child_nodes(whole_data, is_top_level=True)

    # Save the updated data to a new JSON file
    with open('output/cpc/abstract_cpc12/cpc_abstract_round2_iter1.json', 'w') as output_file:
        json.dump(data, output_file, indent=4)




        