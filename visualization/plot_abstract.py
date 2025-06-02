import json
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill






def process_hierarchy(data, label0="", lbl0_code="", lbl0_count=0):
    rows = []
    
    # Traverse each level and append rows
    def traverse(node, level, labels, codes, counts):
        label0, label1, label2 = labels
        lbl0_code, lbl1_code, lbl2_code = codes
        lbl0_count, lbl1_count, lbl2_count = counts

        # Base node values
        row = {
            "lbl0_count": lbl0_count,
            "label0": label0,
            "lbl1_code": lbl0_code,
            "lbl1_count": lbl1_count,
            "label1": label1,
            "lbl2_code": lbl1_code,
            "label2": label2,
            "lbl2_count": lbl2_count,
        
        }
        
        # Check for children to traverse deeper
        if "children" in node and node["children"]:
            for child_code, child_node in node["children"].items():
                # Populate values for the next level down
                if level == 0:
                    traverse(child_node, level + 1, 
                             [node.get("label", ""), child_node.get("label", ""), ""], 
                             [child_code, child_code, ""], 
                             [node.get("count", 0), child_node.get("count", 0), 0])
                elif level == 1:
                    traverse(child_node, level + 1, 
                             [label0, label1, child_node.get("label", "")], 
                             [lbl0_code, child_code, child_code], 
                             [lbl0_count, node.get("count", 0), child_node.get("count", 0)])
                elif level == 2:
                    row.update({
                        "lbl0_count": lbl0_count,
                        "label0": label0,
                        "lbl1_code": lbl0_code,
                        "lbl1_count": lbl1_count,
                        "label1": label1,
                        "lbl2_code": lbl1_code,
                        "label2": child_node.get("label", ""),
                        "lbl2_count": child_node.get("count", 0)
                        
                    })
                    rows.append(row.copy())
        else:
            # If there are no children, it's a leaf node
            if level == 1:
                row.update({
                    "lbl0_count": lbl0_count,
                    "label0": label0,
                    "lbl1_code": lbl0_code,
                    "lbl1_count": lbl1_count,
                    "label1": node.get("label", ""),
                    "lbl2_code": lbl1_code,
                })
            elif level == 2:
                row.update({
                    "lbl0_count": lbl0_count,
                    "label0": label0,
                    "lbl1_code": lbl0_code,
                    "lbl1_count": lbl1_count,
                    "label1": label1,
                    "lbl2_code": lbl1_code,
                    "label2": node.get("label", ""),
                    "lbl2_count": lbl2_count,
                    
                })
            rows.append(row.copy())
    
    # Start traversal from the top-level node(s)
    for top_code, top_node in data.items():
        traverse(top_node, 0, [top_node.get("label", ""), "", ""], [top_code, "", ""], [top_node.get("count", 0), 0, 0])
    
    return rows

if __name__ == "__main__":
# Load your JSON data
    with open('output/cpc/abstract_cpc13/cpc_abstract_round11_iter1_refined.json', 'r') as f:
        data = json.load(f)
    # Process the JSON to create structured data
    rows = process_hierarchy(data)
    df = pd.DataFrame(rows)

    # Write DataFrame to Excel without any additional formatting
    filename = "output/cpc/abstract_cpc13/cpc_abstract_round11_iter1_refined.xlsx"
    df.to_excel(filename, index=False)

    print("Excel file created as 'structured_output.xlsx'.")