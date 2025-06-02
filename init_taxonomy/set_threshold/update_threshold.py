import json
import numpy as np



def calculate_threshold(counts, z_threshold=-1):
    """
    Calculates a threshold based on Z-score analysis.

    Parameters:
        counts (list): List of count values of sibling nodes.
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

def update_thresholds(data, z_threshold=-1):
    """
    Recursively traverses the JSON data, calculates thresholds based on sibling counts,
    and updates the threshold in each node with a count.

    Parameters:
        data (dict): The JSON data structure.
        z_threshold (float): The Z-score threshold to determine significant outliers.

    Returns:
        dict: The modified JSON data with thresholds updated at each level.
    """
    def recursive_update_thresholds(node):
        if "children" in node and isinstance(node["children"], dict):
            counts = [child.get("count", 0) for child in node["children"].values()]
            threshold = calculate_threshold(counts, z_threshold)

            for key, child in node["children"].items():
                # Update the existing threshold value
                child["threshold"] = threshold
                recursive_update_thresholds(child)

    for key, root_node in data.items():
        if "count" in root_node:
            root_counts = [root.get("count", 0) for root in data.values()]
            root_threshold = calculate_threshold(root_counts, z_threshold)
            root_node["threshold"] = root_threshold

        recursive_update_thresholds(root_node)

    return data

if __name__ == "__main__":
    with open('data/cpc/label_count.json', 'r') as file:
        data = json.load(file)


    data_with_updated_thresholds = update_thresholds(data, z_threshold=-1)

    with open('output/cpc/abstract_cpc/label_count_updated.json', 'w') as file:
        json.dump(data_with_updated_thresholds, file, indent=4)

    print("Thresholds have been updated and saved")
