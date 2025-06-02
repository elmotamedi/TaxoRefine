import json
from openai import OpenAI
import os
import ast

# from prompts import PROMPT_TEMPLATES
from prompts2 import PROMPT_TEMPLATES
from configs.config import api_key

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key= api_key
)

def chat_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def generate_representative_label(candidate_code, candidate_label, sibling_code, sibling_label, parent_label):
    """
    Generates a representative label for merged categories.
    """
    prompt = PROMPT_TEMPLATES["representative_label"].format(
        candidate_code= candidate_code,
        candidate_label = candidate_label,
        sibling_code  =sibling_code,
        sibling_label = sibling_label,
        parent_label=parent_label
    )
    return chat_gpt(prompt)

def find_merge_candidates(nodes):
    """
    Identifies nodes where count <= threshold.
    
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


    
    print(f"Merged {candidate_code} and {sibling_code} with label '{representative_label}'")

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


def merge_entities(data, candidate_code, sibling_code, representative_label):
    """
    Updates the JSON data by merging two classes and saving the result in the parent's children dictionary.

    Parameters:
        data (dict): The hierarchical JSON data as a dictionary.
        candidate_code (str): Code of the first node to merge.
        sibling_code (str): Code of the second node to merge.
        representative_label (str): New label for the merged node.
    """
    # Check if both nodes are at the top level
    if candidate_code in data and sibling_code in data:
        # Top-level merge logic
        candidate_node = data[candidate_code]
        sibling_node = data[sibling_code]
        parent_node = data  # Treat the entire `data` as the parent

    else:
        # Nested level merge logic
        candidate_node = find_node_by_key(data, candidate_code)
        sibling_node = find_node_by_key(data, sibling_code, parent_code=candidate_node.get("parent_code") if candidate_node else None)
        parent_node = find_node_by_key(data, candidate_node['parent_code'])

        # Check if both nodes share the same parent
        if not candidate_node or not sibling_node or parent_node is None:
            print(f"Could not find nodes {candidate_code} and {sibling_code} with the same parent.")
            return data

    # Calculate merged properties
    merged_children = {**candidate_node.get("children", {}), **sibling_node.get("children", {})}
    merged_count = candidate_node.get("count", 0) + sibling_node.get("count", 0)
    merged_threshold = candidate_node.get("threshold", 0)  # Using candidate threshold as default

    # Create the merged node
    merged_key = f"{candidate_code},{sibling_code}"
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
        # Remove the original candidate and sibling nodes from `data`
        if candidate_code in data:
            del data[candidate_code]
        if sibling_code in data:
            del data[sibling_code]
    else:
        # For nested nodes, modify `parent_node`'s children
        parent_node["children"][merged_key] = merged_node
        # Remove original candidate and sibling nodes from parent's children
        if candidate_code in parent_node["children"]:
            del parent_node["children"][candidate_code]
        if sibling_code in parent_node["children"]:
            del parent_node["children"][sibling_code]

    print(f"Merged {candidate_code} and {sibling_code} with label '{representative_label}'")

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



def decide_to_merge(candidate, data, parent_label=None, is_top_level=False, prompt_template=None):
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

    response = chat_gpt(prompt)
    
    if response in ('None', None, "'None'", 'none', '"none"'):
        return None
    
    try:
        response_dict = ast.literal_eval(response)
        return response_dict
    except (ValueError, SyntaxError):
        return response  # Return as-is if it’s not a valid dictionary

def process_level(nodes, parent_label=None, is_top_level=True, prompt_template=None):
    merge_candidates = find_merge_candidates(nodes)

    for candidate in merge_candidates:
        merge_decision = decide_to_merge(candidate, nodes, parent_label=parent_label, is_top_level=is_top_level, prompt_template=prompt_template)
        candidate_code = candidate["code"]
        candidate_label = candidate["label"]
        
        if merge_decision:
            sibling_code = merge_decision["sibling_code"]
            sibling_label =  merge_decision["sibling_label"]

            # Generate a representative label for the merged category
            representative_label = generate_representative_label(candidate_code, candidate_label, sibling_code, sibling_label, parent_label)
            representative_label = representative_label.strip("'\"")
            print(f"{candidate_code} ({candidate_label}) will be merged with {sibling_code} ({sibling_label}) "
                  f"with the representative label: {representative_label}")


            # Update the data with the merged label and counts
            merge_entities( data, candidate_code, sibling_code, representative_label)
        else:
            print(f"decided not to merge {candidate_code} ({candidate_label}) woth siblings")

    for code, node in nodes.items():
        children = node.get("children", {})
        if children:
            process_level(children, parent_label=node.get("label"), is_top_level=False, prompt_template=prompt_template)




if __name__ == "__main__":
    # # Load the JSON file with thresholds
    with open('output/cpc/label_count_with_thresholds_parents.json', 'r') as file:
        data = json.load(file)
    # Use the prompt template from prompts.py
    prompt_template = PROMPT_TEMPLATES["merge_decision"]

    # Start processing from the top level
    process_level(data, is_top_level=True, prompt_template=prompt_template)

    # Save the updated data to a new JSON file
    with open('output/cpc/cpc_abstract_iter1.json', 'w') as output_file:
        json.dump(data, output_file, indent=4)