import json
from openai import OpenAI
import os
import ast
from configs.config import api_key

from .prompts import PROMPT_TEMPLATES

client = OpenAI(
    api_key = api_key
)

# Base cache directory
CACHE_DIR = "prompt_cache_cnt_based"

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
        print(f"Cache saved to {cache_file}.")
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

def generate_representative_label_manual(candidate_code, candidate_label, sibling_code, sibling_label, parent_label):
    # Ensure labels are stripped of whitespace
    candidate_label = candidate_label.strip()
    sibling_label = sibling_label.strip()
    
    # Handle empty or None values
    if not candidate_label and not sibling_label:
        return ""
    if not candidate_label:
        return sibling_label
    if not sibling_label:
        return candidate_label
    
    # Concatenate and return
    return f"{candidate_label}; {sibling_label}"

    

def generate_representative_label(candidate_code, candidate_label, sibling_code, sibling_label, parent_label):
    """
    Generates a representative label for merged categories.
    """
    prompt = PROMPT_TEMPLATES["representative_label_for_merge"].format(
        candidate_code= candidate_code,
        candidate_label = candidate_label,
        sibling_code  =sibling_code,
        sibling_label = sibling_label,
        parent_label=parent_label
    )
    return chat_gpt(prompt, "generate_representative_label")

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
    merged_key = f"{candidate_code}_{sibling_code}"

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


def merge_entities(data, candidate_code, sibling_code, representative_label, merge_candidates):
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
        if candidate_node is None:
            print(f"Error: Node with code {candidate_code} not found.")
            return merge_candidates
        sibling_node = find_node_by_key(data, sibling_code, parent_code=candidate_node.get("parent_code") if candidate_node else None)
        if sibling_node is None:
            sibling_node = find_node_by_key(data, sibling_code, parent_code=candidate_node.get("parent_code") if candidate_node else None)
            print(f"Error: Sibling code for node {candidate_code} is missing.")
            return merge_candidates
        parent_node = find_node_by_key(data, candidate_node['parent_code'])
        if parent_node is None:
            print(f"Error: Parent code for node {candidate_code} is missing.")
            return merge_candidates

        # Check if both nodes share the same parent
        if not candidate_node or not sibling_node or parent_node is None:
            print(f"Could not find nodes {candidate_code} and {sibling_code} with the same parent.")
            return data

    # Calculate merged properties
    merged_children = {**candidate_node.get("children", {}), **sibling_node.get("children", {})}
    merged_count = candidate_node.get("count", 0) + sibling_node.get("count", 0)
    merged_threshold = candidate_node.get("threshold", 0)  # Using candidate threshold as default

    # Create the merged node
    merged_key = f"{candidate_code}_{sibling_code}"
    merged_node = {
        "label": representative_label,
        "children": merged_children,
        "count": merged_count,
        "threshold": merged_threshold,
        "parent_code": candidate_node.get("parent_code", "")
    }
    # # merged_element is to be used for updating merge_candidates
    # merge_elemnt = {
    #     "code": merged_key,        
    #     "label": representative_label,
    #     "children": merged_children,
    #     "count": merged_count,
    #     "threshold": merged_threshold,
    #     "parent_code": candidate_node.get("parent_code", "")
    # }

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

    ## update the merged_keys if these keys are in the candidate for merge 
    merge_candidates = [candidate for candidate in merge_candidates if candidate["code"] != candidate_code]
    merge_candidates = [candidate for candidate in merge_candidates if candidate["code"] != sibling_code]
    merge_candidates


    return merge_candidates



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






import ast

def decide_to_merge(candidate, data, parent_label=None, is_top_level=False, prompt_template=None):
    candidate_code = candidate.get("code")
    candidate_label = candidate.get("label")
    labels_info = collect_labels(candidate_code, data, parent_label=parent_label, is_top_level=is_top_level)
    if (len(labels_info['sibling_codes']) == 0):
        return "No Siblings"

    # Format the chosen prompt template with the relevant details
    prompt = prompt_template.format(
        parent_label=labels_info['parent_label'],
        candidate_label=labels_info['candidate_label'],
        sibling_labels=labels_info['sibling_labels'],
        sibling_codes=labels_info['sibling_codes']
    )

    response = chat_gpt(prompt, "decide_to_merge").strip()

    # Return None if response explicitly indicates no merge
    if response.lower() in (None, "'none'", 'none', '"none"'):
        print("decide not to merge.")
        return None

    try:
        # Attempt to parse the response as a dictionary
        response_dict = ast.literal_eval(response)
        if isinstance(response_dict, dict):
            # Clean the dictionary values (strip strings)
            cleaned_dict = {k: v.strip() if isinstance(v, str) else v for k, v in response_dict.items()}
            # Validate sibling code
            if cleaned_dict.get('sibling_code') not in labels_info['sibling_codes']:
                print("Error: GPT returned an invalid sibling code!")
                # return decide_to_merge(candidate, data, parent_label=None, is_top_level=False, prompt_template=None)
                return None
            return cleaned_dict
        else:
            print("Error: Response is not a valid dictionary.")
            return None
    except (ValueError, SyntaxError):
        print("Error: Response could not be parsed.")
        return None


def process_level(whole_data, nodes, parent_label=None, is_top_level=True, prompt_template=None):
    merge_candidates = find_merge_candidates(nodes)

    i = 0
    # Manually create the loop since merge_candidates is updated inside the loop
    while i < len(merge_candidates):
        candidate = merge_candidates[i]
        merge_decision= decide_to_merge(candidate, nodes, parent_label=parent_label, is_top_level=is_top_level, prompt_template=prompt_template)
        candidate_code = candidate["code"]
        candidate_label = candidate["label"]
        if (merge_decision == "No Siblings"):
            i = 0
            merge_candidates = []
            print(f"No sibling of {candidate_code}")
        
        elif merge_decision:
            sibling_code = merge_decision["sibling_code"]
            sibling_label =  merge_decision["sibling_label"]

            # Generate a representative label for the merged category
            representative_label = generate_representative_label(candidate_code, candidate_label, sibling_code, sibling_label, parent_label)
            representative_label = representative_label.strip("'\"")
            print(f"{candidate_code} ({candidate_label}) will be merged with {sibling_code} ({sibling_label}) "
                  f"with the representative label: {representative_label}")


            # Update the data with the merged label and counts
            merge_candidates = merge_entities( whole_data, candidate_code, sibling_code, representative_label, merge_candidates)
            #Restart the loop to reprocess the updated list
            i = 0
        else:
            print(f"decided not to merge {candidate_code} ({candidate_label}) with siblings")
            i += 1 # Move to the next candidate

    for code, node in nodes.items():
        children = node.get("children", {})
        if children:
            process_level(whole_data, children, parent_label=node.get("label"), is_top_level=False, prompt_template=prompt_template)




if __name__ == "__main__":
    # # Load the JSON file with thresholds
    with open('output/cpc/abstract_cpc7/cpc_abstract_round1_iter0_updated.json', 'r') as file:
        data = json.load(file)
    whole_data  = data

    # Use the prompt template from prompts.py
    prompt_template = PROMPT_TEMPLATES["merge_decision"]

    # Start processing from the top level
    process_level(whole_data, data, is_top_level=True, prompt_template=prompt_template)

    # Save the updated data to a new JSON file
    with open('output/cpc/abstract_cpc7/cpc_abstract_round1_iter1.json', 'w') as output_file:
        json.dump(data, output_file, indent=4)


        