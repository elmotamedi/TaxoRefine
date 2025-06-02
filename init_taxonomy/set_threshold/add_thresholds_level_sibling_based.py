import json
import numpy as np

def remove_low_count_classes(data, min_count, removed_codes):
    """
    Recursively removes nodes with a count less than the specified threshold
    and records the removed codes.

    Parameters:
        data (dict): The JSON data structure.
        min_count (int): The minimum count threshold. Nodes with count below this value are removed.
        removed_codes (list): List to collect the codes of removed nodes.

    Returns:
        dict: The modified JSON data with low-count nodes removed.
    """
    # Create a new dictionary to store the filtered data
    filtered_data = {}

    for code, item in data.items():
        # Check if the current item has a count and if it meets the minimum count threshold
        if "count" in item and item["count"] < min_count:
            removed_codes.append(code)  # Record the code of the removed item
            continue  # Skip this item if it doesn't meet the threshold

        # If the item has children, recursively apply the function
        if "children" in item and isinstance(item["children"], dict):
            item["children"] = remove_low_count_classes(item["children"], min_count, removed_codes)

        # Add the item to the filtered data if it meets the threshold or has valid children
        filtered_data[code] = item

    return filtered_data

def calculate_threshold(counts, z_threshold=-1):
    """
    Calculates a threshold based on Z-score analysis.

    Parameters:
        counts (list): List of count values.
        z_threshold (float): The Z-score threshold to determine significant outliers.

    Returns:
        float: The threshold value.
    """
    if not counts:
        return 0

    mean_count = np.mean(counts)
    std_count = np.std(counts)
    threshold_value = mean_count + (z_threshold * std_count)
    return max(0, int(threshold_value))

def add_thresholds_sibling_based(data, z_threshold=-1):
    """
    Recursively traverses the JSON data, calculates thresholds based on sibling counts,
    and adds the sibling threshold to each node with a count.

    Parameters:
        data (dict): The JSON data structure.
        z_threshold (float): The Z-score threshold to determine significant outliers.

    Returns:
        dict: The modified JSON data with sibling thresholds added.
    """
    def recursive_add_thresholds(node):
        # If node has children, calculate threshold for each child based on sibling counts
        if "children" in node and isinstance(node["children"], dict):
            counts = [child.get("count", 0) for child in node["children"].values()]
            threshold = calculate_threshold(counts, z_threshold)

            # Process each child
            for key, child in node["children"].items():
                # Add sibling threshold for each child node
                child["sibling_threshold"] = threshold
                # Recur into the child node to process deeper levels
                recursive_add_thresholds(child)

    # Start the recursion with the root node
    for key, root_node in data.items():
        if "count" in root_node:
            # Calculate threshold for the top-level nodes
            root_counts = [root.get("count", 0) for root in data.values()]
            root_threshold = calculate_threshold(root_counts, z_threshold)
            root_node["sibling_threshold"] = root_threshold

        # Apply thresholds recursively to the rest of the hierarchy
        recursive_add_thresholds(root_node)

    return data

def add_thresholds_level_based(data, z_threshold=-1):
    """
    Recursively traverses the JSON data, calculates thresholds based on level counts,
    and adds the level-based threshold to each node with a count.

    Parameters:
        data (dict): The JSON data structure.
        z_threshold (float): The Z-score threshold to determine significant outliers.

    Returns:
        dict: The modified JSON data with level-based thresholds added.
    """
    def collect_all_level_counts(node, current_level, level_counts):
        """
        Collect counts for all nodes grouped by levels.
        """
        if current_level not in level_counts:
            level_counts[current_level] = []

        if "count" in node:
            level_counts[current_level].append(node["count"])

        if "children" in node and isinstance(node["children"], dict):
            for child in node["children"].values():
                collect_all_level_counts(child, current_level + 1, level_counts)

    def recursive_add_thresholds(node, current_level, level_thresholds):
        """
        Add level-based thresholds to nodes based on pre-computed thresholds for each level.
        """
        if current_level in level_thresholds:
            node["level_threshold"] = level_thresholds[current_level]

        if "children" in node and isinstance(node["children"], dict):
            for child in node["children"].values():
                recursive_add_thresholds(child, current_level + 1, level_thresholds)

    # Step 1: Collect all counts grouped by levels
    level_counts = {}
    for root in data.values():
        collect_all_level_counts(root, 0, level_counts)

    # Step 2: Calculate level-based thresholds
    level_thresholds = {}
    for level, counts in level_counts.items():
        level_thresholds[level] = calculate_threshold(counts, z_threshold)

    # Step 3: Add thresholds to nodes
    for key, root_node in data.items():
        recursive_add_thresholds(root_node, 0, level_thresholds)

    return data

def assign_maximum_threshold(data):
    """
    Assigns the maximum of sibling and level thresholds to the final threshold field and removes the sibling_threshold and level_threshold fields.

    Parameters:
        data (dict): The JSON data structure.

    Returns:
        dict: The modified JSON data with the maximum threshold assigned.
    """
    def recursive_assign_threshold(node):
        if "sibling_threshold" in node and "level_threshold" in node:
            node["threshold"] = max(node["sibling_threshold"], node["level_threshold"])
            del node["sibling_threshold"]
            del node["level_threshold"]

        if "children" in node and isinstance(node["children"], dict):
            for child in node["children"].values():
                recursive_assign_threshold(child)

    for root in data.values():
        recursive_assign_threshold(root)

    return data



if __name__ == "__main__":
    # Load the JSON data (replace 'input.json' with your actual file path)
    with open('output/cpc/abstract_cpc8/cpc_abstract_round6_iter0.json', 'r') as file:
        data = json.load(file)


    data_with_sibling_thresholds = add_thresholds_sibling_based(data, z_threshold=-2)
    data_with_level_thresholds = add_thresholds_level_based(data_with_sibling_thresholds, z_threshold=-2)
    data_with_final_thresholds = assign_maximum_threshold(data_with_level_thresholds)

    # Save the modified data with thresholds to a new JSON file
    with open('output/cpc/abstract_cpc8/cpc_abstract_round6_iter0_updated.json', 'w') as file:
        json.dump(data_with_final_thresholds, file, indent=4)


    print("Thresholds have been added and saved")
