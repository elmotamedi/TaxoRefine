import json
import os
import re

# Function to add items without hierarchy initially
def add_to_hierarchy_flat(hierarchy, code, label):
    hierarchy[code] = {"label": label, "children": {}}

# Function to parse file and build a flat dictionary structure
def parse_and_build_hierarchy_flat(file_path, hierarchy):
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # Use regex to split on one or more whitespace characters (tabs or spaces)
            parts = re.split(r'\s{2,}', line.strip())  # Split on two or more spaces/tabs
            code = parts[0].strip() if len(parts) > 0 else ""
            # Extract label and remove any text in parentheses
            label = parts[1].strip() if len(parts) > 1 else ""
            label = re.split(r'\s*\(', label)[0]  # Keep only text before '('
            
            # Ignore codes longer than 4 characters
            if len(code) > 4:
                continue
            
            # Add each code as a top-level item for now
            add_to_hierarchy_flat(hierarchy, code, label)
    
    return hierarchy

# Post-processing to nest each code under its correct parent
def nest_hierarchy(flat_hierarchy):
    nested_hierarchy = {}

    # Helper function to find the parent code
    def get_parent_code(code):
        if len(code) <= 3:
            return code[0]  # Single character for top-level codes like "A"
        return code[:-3]  # Remove the last level (3 characters)

    # Place each code under its parent in the hierarchy
    for code, data in flat_hierarchy.items():
        current_level = nested_hierarchy
        # Process each part of the code incrementally (e.g., "A", "A01", "A01B")
        for i in range(0, len(code), 3):
            part = code[:i+3]
            # If this is the final part, set the label and children
            if i + 3 == len(code):
                if part not in current_level:
                    current_level[part] = {"label": data["label"], "children": {}}
                current_level[part]["label"] = data["label"]
            else:
                # Otherwise, ensure the part exists and move deeper
                if part not in current_level:
                    current_level[part] = {"label": flat_hierarchy.get(part, {}).get("label", ""), "children": {}}
                current_level = current_level[part]["children"]

    return nested_hierarchy

# Directory containing the text files
input_directory = 'data/cpc/'  # Replace with your directory path
output_file = 'output/cpc/labels.json'

# Initialize an empty hierarchy
flat_hierarchy = {}

# Process each file in the directory to build a flat hierarchy
for filename in os.listdir(input_directory):
    file_path = os.path.join(input_directory, filename)
    if os.path.isfile(file_path) and file_path.endswith('.txt'):
        print(f"Processing {filename}...")
        flat_hierarchy = parse_and_build_hierarchy_flat(file_path, flat_hierarchy)

# Post-process the flat hierarchy into a nested structure
nested_hierarchy = nest_hierarchy(flat_hierarchy)

# Write the structured JSON data to file
with open(output_file, 'w', encoding='utf-8') as file:
    json.dump(nested_hierarchy, file, indent=4, ensure_ascii=False)

print(f"JSON data has been saved to {output_file}")
