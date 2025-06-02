
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
print(sys.path)
import json
from openai import OpenAI

import ast
from configs.config import api_key
from prompts import PROMPT_TEMPLATES

client = OpenAI(
    api_key = api_key
)

# Base cache directory
CACHE_DIR = "prompt_cache_meta"

# Ensure the cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_file(function_name):
    """Generate a cache file path based on the function name."""
    return os.path.join(CACHE_DIR, f"{function_name}_prompts.json")

def load_cache(function_name):
    """Load the cache for a specific function."""
    cache_file = get_cache_file(function_name)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print(f"Cache file {cache_file} is corrupted. Reinitializing.")
            return {}
    return {}

def save_cache(function_name, cache):
    """Save the cache for a specific function."""
    cache_file = get_cache_file(function_name)
    try:
        with open(cache_file, "w") as file:
            json.dump(cache, file)
        # print(f"Cache saved to {cache_file}.")
    except Exception as e:
        print(f"Error saving cache: {e}")

def chat_gpt(prompt, function_name):
    """Send a prompt to GPT-4 and cache the response."""
    # Load the cache specific to the calling function
    prompt_cache = load_cache(function_name)

    # Check if the prompt exists in the cache
    if prompt in prompt_cache:
        print(f"Cache hit for prompt in {function_name}.")
        return prompt_cache[prompt]

    # If not in cache, make the API call
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.choices[0].message.content.strip()

    # Cache the response
    prompt_cache[prompt] = result
    save_cache(function_name, prompt_cache)
    return result




def generate_representative_label(candidate_code, candidate_label, sibling_codes, sibling_labels, parent_label):
    """
    Generates a representative label for merged categories.
    """
    prompt = PROMPT_TEMPLATES["representative_label"].format(
        candidate_code= candidate_code,
        candidate_label = candidate_label,
        sibling_codes  =sibling_codes,
        sibling_labels = sibling_labels,
        parent_label=parent_label
    )
    return chat_gpt(prompt, "representative_label_based_on_meta_characteristics")

def find_meta_candidates(nodes):
    """
    Identifies nodes for merge -> always apend
    
    Parameters:
        nodes (dict): A dictionary of nodes to check for merge candidates.

    Returns:
        list: A list of merge candidate nodes, each as a dictionary with details.
    """
    candidates = []
    for code, node in nodes.items():
        count = node.get("count", None)
        threshold = node.get("threshold", None)
        if count is not None and threshold is not None and count <= threshold:
            candidates.append({
                "code": code,
                "label": node.get("label", "No Label"),
                "count": count,
                "threshold": threshold,
                "children": node.get("children", {})
            })
        else:
            candidates.append({
                "code": code,
                "label": node.get("label", "No Label"),
                "count": count,
                "threshold": threshold,
                "children": node.get("children", {})
            })
        #always append
        # candidates.append({
        #         "code": code,
        #         "label": node.get("label", "No Label"),
        #         "count": count,
        #         "threshold": threshold,
        #         "children": node.get("children", {})
        # })
    return sorted(candidates, key=lambda x: x["count"])

def find_parent_node(data, parent_code):
    """
    Finds the parent node in the data based on the parent_code.
    
    Parameters:
        data (dict): The hierarchical JSON data.
        parent_code (str): The code of the parent node.
    
    Returns:
        dict: The parent node if found, else None.
    """
    for code, node in data.items():
        if code == parent_code:
            return node
        elif "children" in node:
            found_parent = find_parent_node(node["children"], parent_code)
            if found_parent:
                return found_parent
    return None

def update_json(data, candidate_code, sibling_code, representative_label):
    """
    Updates the JSON data by merging two classes and saving the result in the parent's children dictionary.
    
    Parameters:
        data (dict): The hierarchical JSON data.
        candidate_code (str): Code of the first node to merge.
        sibling_code (str): Code of the second node to merge.
        representative_label (str): New label for the merged node.
    """
    merged_key = f"{candidate_code}, {sibling_code}"

    if len(candidate_code) == 1:
        #get the union of children
        children = {**data[candidate_code]['children'] , ** data[sibling_code]['children']}
        cnt = data[candidate_code]['count'] + data[sibling_code]['count']
        threshold = data[candidate_code]['threshold'] + data[sibling_code]['threshold']
        # Remove the original candidate and sibling nodes from the parent node's children
        del data[candidate_code]
        del data[sibling_code]
        # Create the merged node under the parent
        data[merged_key] = {
        "label": representative_label,
        "children": children,
        "count": cnt,
        "threshold": threshold
        }

    if len(candidate_code) == 3:
        lvl0_parent_code = candidate_code[0]
        children = {**data[lvl0_parent_code]['children'][candidate_code]['children'] , **data[lvl0_parent_code]['children'][sibling_code]['children']}
        cnt = data[lvl0_parent_code]['children'][candidate_code]['count'] + data[lvl0_parent_code]['children'][sibling_code]['count']
        threshold = data[lvl0_parent_code]['children'][candidate_code]['threshold'] + data[lvl0_parent_code]['children'][sibling_code]['threshold']
        # Remove the original candidate and sibling nodes from the parent node's children
        del data[lvl0_parent_code]['children'][candidate_code]
        del data[lvl0_parent_code]['children'][sibling_code]
        # Create the merged node under the parent
        data[lvl0_parent_code]['children'][merged_key] = {
        "label": representative_label,
        "children": children,
        "count": cnt,
        "threshold": threshold
        }
    if len(candidate_code) == 4:
        lvl0_parent_code = candidate_code[0]
        lvl1_parent_code = candidate_code[0:3]
        children = {**data[lvl0_parent_code]['children'][lvl1_parent_code]['children'][candidate_code]['children'], **data[lvl0_parent_code]['children'][lvl1_parent_code]['children'][sibling_code]['children']}
        cnt = data[lvl0_parent_code]['children'][lvl1_parent_code]['children'][candidate_code]['count'] + data[lvl0_parent_code]['children'][lvl1_parent_code]['children'][sibling_code]['count']
        threshold = data[lvl0_parent_code]['children'][lvl1_parent_code]['children'][candidate_code]['threshold'] + data[lvl0_parent_code]['children'][lvl1_parent_code]['children'][sibling_code]['threshold']
        # Remove the original candidate and sibling nodes from the parent node's children
        del data[lvl0_parent_code]['children'][lvl1_parent_code]['children'][candidate_code]
        del data[lvl0_parent_code]['children'][lvl1_parent_code]['children'][sibling_code]
            # Create the merged node under the parent
        data[lvl0_parent_code]['children'][lvl1_parent_code]['children'][merged_key] = {
        "label": representative_label,
        "children": children,
        "count": cnt,
        "threshold": threshold
        }


    
    # print(f"Merged {candidate_code} and {sibling_code} with label '{representative_label}'")

    return data

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


def merge_entities(data, candidate_code, sibling_codes, representative_label):
    """
    Updates the JSON data by merging a candidate node with multiple sibling nodes
    and saving the result in the parent's children dictionary.

    Parameters:
        data (dict): The hierarchical JSON data as a dictionary.
        candidate_code (str): Code of the node to merge.
        sibling_codes (list): List of codes of sibling nodes to merge with the candidate node.
        representative_label (str): New label for the merged node.
    """
    # Check if candidate node is at the top level
    if candidate_code in data:
        candidate_node = data[candidate_code]
        parent_node = data  # Top-level parent
    else:
        # Nested level candidate node
        candidate_node = find_node_by_key(data, candidate_code)
        parent_node = find_node_by_key(data, candidate_node.get("parent_code")) if candidate_node else None

    if not candidate_node or not parent_node:
        # print(f"Candidate node {candidate_code} or its parent not found.")
        return data

    # Initialize merged properties
    merged_children = candidate_node.get("children", {}).copy()
    merged_count = candidate_node.get("count", 0)
    merged_threshold = candidate_node.get("threshold", 0)  # Default to candidate threshold

    # Iterate over sibling codes
    for sibling_code in sibling_codes:
        # Check if sibling node is at the top level
        if sibling_code in data:
            sibling_node = data[sibling_code]
        else:
            sibling_node = find_node_by_key(data, sibling_code, parent_code=candidate_node.get("parent_code"))

        if not sibling_node:
            # print(f"Sibling node {sibling_code} not found. Skipping.")
            continue

        # Merge properties of sibling node
        merged_children.update(sibling_node.get("children", {}))
        merged_count += sibling_node.get("count", 0)

        # Remove sibling node from its parent
        if sibling_code in data:
            del data[sibling_code]
        elif sibling_code in parent_node.get("children", {}):
            del parent_node["children"][sibling_code]

    # Create the merged node
    merged_key = f"{candidate_code}," + ",".join(sibling_codes)
    merged_node = {
        "key": merged_key,
        "label": representative_label,
        "children": merged_children,
        "count": merged_count,
        "threshold": merged_threshold,
        "parent_code": candidate_node.get("parent_code", "")
    }

    # Update `parent_code` for each child in the merged node
    for child_code in merged_node["children"]:
        merged_node["children"][child_code]["parent_code"] = merged_key

    # Update the parent's children dictionary
    if parent_node == data:
        # For top-level nodes, modify `data` directly
        data[merged_key] = merged_node
        # Remove the original candidate node from `data`
        if candidate_code in data:
            del data[candidate_code]
    else:
        # For nested nodes, modify `parent_node`'s children
        parent_node["children"][merged_key] = merged_node
        # Remove the original candidate node from parent's children
        if candidate_code in parent_node["children"]:
            del parent_node["children"][candidate_code]

    # print(f"Merged {candidate_code} with siblings {sibling_codes} under label '{representative_label}'")

    return data



def collect_labels(candidate_code, data, parent_label=None, is_top_level=False):
    labels_info = {
        "parent_label": parent_label if parent_label else None,
        "candidate_label": None,
        "sibling_codes": [],
        "sibling_labels": [],
        "children_labels": []
    }
    
    # Get candidate node and label information
    candidate_node = data.get(candidate_code, {})
    labels_info["candidate_label"] = candidate_node.get("label", "No Label")

    # Collect children labels of the candidate node (if any)
    labels_info["children_labels"] = [
        child.get("label", "No Label") for child in candidate_node.get("children", {}).values()
    ]

    # Collect sibling codes and labels from other nodes at the same level in `data`
    labels_info["sibling_codes"] = [
        sibling_code
        for sibling_code in data.keys()
        if sibling_code != candidate_code
    ]
    labels_info["sibling_labels"] = [
        sibling.get("label", "No Label")
        for sibling_code, sibling in data.items()
        if sibling_code != candidate_code
    ]

    return labels_info



def decide_to_remove(candidate, data, parent_label=None, is_top_level=False, prompt_template=None):
    candidate_code = candidate.get("code")
    candiate_label = candidate.get("label")
    labels_info = collect_labels(candidate_code, data, parent_label=parent_label, is_top_level=is_top_level)

    # Format the chosen prompt template with the relevant details
    prompt = prompt_template.format(
        parent_label=labels_info['parent_label'],
        candidate_label=labels_info['candidate_label'],
        sibling_labels=labels_info['sibling_labels'],
        sibling_codes=labels_info['sibling_codes']
    )

    response = chat_gpt(prompt, "decision_on_meta_characteristics" )
    
    if response is None or str(response).lower() in ('none', "'none'", '"none"'):
        # print("in if")
        return None
    
    try:
        if response.strip().lower() == "remove":
            return "Remove"
        elif response.strip().lower() == "none":
            return None
        else:
            response_dict = ast.literal_eval(response)
            if not response_dict:
                print("return none!")
                return None
            return response_dict
    except (ValueError, SyntaxError):
        # Print an error if parsing fails
        print("Parsing error. Returning raw response.")
    return None

def remove_node_and_children(data, candidate_code):
    """
    Recursively removes a candidate node and all its children from the JSON data structure.
    If the candidate node is the only child, its parent is also removed.

    Parameters:
        data (dict): The hierarchical JSON data.
        candidate_code (str): The code of the candidate node to be removed.

    Returns:
        dict: The updated data with the specified node and its children removed.
    """
    # Check if candidate node exists at the top level
    if candidate_code in data:
        # Remove the node at the top level
        del data[candidate_code]
        print(f"Removed top-level node {candidate_code}")
        return data

    # Recursively look for the node in children
    for code, node in list(data.items()):
        if "children" in node and candidate_code in node["children"]:
            # Remove the candidate node
            del node["children"][candidate_code]
            print(f"Removed node {candidate_code} from parent {code}")

            # Check if the parent node now has no children
            if not node["children"]:  # If parent has no remaining children
                print(f"Removing parent node {code} as it has no remaining children.")
                remove_node_and_children(data, code)  # Recursively remove the parent

            return data
        elif "children" in node:
            # Recursively process deeper levels
            updated_children = remove_node_and_children(node["children"], candidate_code)
            if updated_children is not None:
                return data

    return data



def process_level(nodes, parent_label=None, is_top_level=True, prompt_template=None, removed_groups=None):
    """
    Processes each level of the JSON hierarchy, making decisions to retain or remove nodes based on LLM prompts.

    Parameters:
        nodes (dict): The hierarchical JSON data.
        parent_label (str): The label of the parent node, if any.
        is_top_level (bool): Whether the current level is the top level of the hierarchy.
        prompt_template (str): The prompt template to use for LLM decisions.
        removed_groups (list): A list to track removed groups.
    """
    # Ensure removed_groups is initialized as an empty list if not provided
    if removed_groups is None:
        removed_groups = []

    # Find candidates for removal
    remove_candidates = find_meta_candidates(nodes)

    # Process each candidate for removal
    for candidate in remove_candidates:
        remove_decision = decide_to_remove(
            candidate, nodes, parent_label=parent_label, is_top_level=is_top_level, prompt_template=prompt_template
        )
        candidate_code = candidate["code"]
        candidate_label = candidate["label"]

        if remove_decision == "Remove":
            print(f"Removing {candidate_code} and all its children.")
            # Add the removed group to the list
            removed_groups.append({
                "code": candidate_code,
                "label": candidate_label,
                "children": candidate.get("children", {})
            })
            remove_node_and_children(nodes, candidate_code)
        else:
            print(f"Decided to retain {candidate_code}")

    # Recursively process child nodes
    for code, node in list(nodes.items()):  # Convert to list to avoid issues with modifying dict during iteration
        children = node.get("children", {})
        if children:
            # Pass the same removed_groups list to the recursive call
            process_level(children, parent_label=node.get("label"), is_top_level=False, prompt_template=prompt_template, removed_groups=removed_groups)

    return removed_groups




if __name__ == "__main__":
    with open('output/cpc/abstract_cpc/label_count_updated_parents.json', 'r') as file:
        data = json.load(file)

    # List to store removed groups
    removed_groups = []
    # Use the prompt template from prompts.py
    prompt_template = PROMPT_TEMPLATES["decision_on_meta_characteristics"]
    removed_groups = process_level(data, is_top_level=True, prompt_template=prompt_template, removed_groups=removed_groups)
    with open('output/cpc/abstract_cpc/cpc_abstract_meta_refined_relavants.json', 'w') as output_file:
        json.dump(data, output_file, indent=4)
    # Save the removed groups to a JSON file
    with open('output/cpc/abstract_cpc/removed_groups_from_meta_refinement.json', 'w') as removed_json_file:
        json.dump(removed_groups, removed_json_file, indent=4)
    # Save the removed groups to a text file
    with open('output/cpc/abstract_cpc/removed_groups_from_meta_refinement.txt', 'w') as removed_text_file:
        for group in removed_groups:
            removed_text_file.write(f"Code: {group['code']}, Label: {group['label']}\n")