import json

def add_parent_code(data, parent_code=""):
    """
    Recursively traverses the JSON hierarchy, adding a 'parent_code' key to each node.
    
    Parameters:
        data (dict): The JSON data to process.
        parent_code (str): The code of the parent node. This is an empty string for root-level nodes.
    
    Returns:
        dict: The updated JSON data with 'parent_code' added to each node.
    """
    updated_data = {}
    for code, node in data.items():
        # Copy the node and add the 'parent_code'
        updated_node = node.copy()
        updated_node["parent_code"] = parent_code
        
        # Recursively add 'parent_code' to children, if they exist
        if "children" in node:
            updated_node["children"] = add_parent_code(node["children"], code)
        
        # Add the updated node to the new structure
        updated_data[code] = updated_node
    
    return updated_data

# Main code
if __name__ == "__main__":
    # Read the JSON file
    with open('output/cpc/abstract_cpc/label_count_updated.json', 'r') as file:
        data = json.load(file)

    # Process the data to add 'parent_code' at each level
    data2 = add_parent_code(data)

    # Save the updated data to a new JSON file
    with open('output/cpc/abstract_cpc/label_count_updated_parents.json', 'w') as output_file:
        json.dump(data2, output_file, indent=4)
