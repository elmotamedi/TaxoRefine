
import sys
import os
import json
import pandas as pd

# Step 1: Get the base directory
script_dir = os.path.abspath(os.path.dirname(__file__))  # Directory of the current script
base_dir = os.path.abspath(os.path.join(script_dir, ".."))  # Parent directory

# Step 2: Build KnowMap_SIC path
taxorefine_path = os.path.join(base_dir, "TaxoRefine")
if not os.path.exists(taxorefine_path):
    raise FileNotFoundError(f"Folder not found in {base_dir}")

sys.path.append(taxorefine_path)

# Import modules
from init_taxonomy.closest_sibling.merge_based_on_common_knowledge_and_size import gen_abstract as gen_abstract_cpc_cnt
from init_taxonomy.closest_sibling.merge_small_leave_nodes import gen_abstract as gen_abstract_cpc_lvl
from init_taxonomy.closest_sibling.merge_based_on_common_knowledge_and_size import prompts as prompts_cnt
from init_taxonomy.closest_sibling.merge_small_leave_nodes import prompts as prompts_lvl

from visualization import plot_abstract
from init_taxonomy.set_threshold import add_thresholds_level_sibling_based

# Step 3: Initialize paths and variables
output_dir = os.path.join(base_dir, "TaxoRefine", "output", "cpc", "abstract_cpc")
input_path = os.path.join(output_dir, "cpc_abstract_meta_refined_relavants.json")

iteration = 1
previous_row_count = -1
round = 1
max_iterations = 100
z_th = -2
subjective_ending_condition = 100
# Step 4: Start looping until row count stabilizes
while previous_row_count > subjective_ending_condition or previous_row_count == -1:
    with open(input_path, 'r') as file:
        data = json.load(file)
    whole_data = data
    while True:
        print(f"\n### Starting Iteration {iteration} ###")
        
        # Generate output filenames for the current iteration
        output_json = os.path.join(output_dir, f"cpc_abstract_round{round}_iter{iteration + 1}.json")
        excel_file = os.path.join(output_dir, f"cpc_abstract_round{round}_iter{iteration + 1}.xlsx")
        updated_json = os.path.join(output_dir, f"cpc_abstract_round{round}_iter{iteration + 1}_updated.json")

        # Process Level
        prompt_template = prompts_cnt.PROMPT_TEMPLATES["merge_decision"]
        gen_abstract_cpc_cnt.process_level(whole_data, data, is_top_level=True, prompt_template=prompt_template)
        with open(output_json, 'w') as output_file:
            json.dump(data, output_file, indent=4)
        print(f"Processed Level and saved: {output_json}")

        # Step 4.2: Visualization
        rows = plot_abstract.process_hierarchy(data)
        df = pd.DataFrame(rows)
        df.to_excel(excel_file, index=False)
        print(f"Visualization saved: {excel_file}")

        # Check row count for termination condition
        current_row_count = len(df)
        print(f"Row Count: {current_row_count}")

        

        # Step 4.3: Add Thresholds
        data_with_sibling_thresholds = add_thresholds_level_sibling_based.add_thresholds_sibling_based(data, z_threshold= z_th)
        data_with_level_thresholds = add_thresholds_level_sibling_based.add_thresholds_level_based(data_with_sibling_thresholds, z_threshold= z_th)
        data_with_final_thresholds = add_thresholds_level_sibling_based.assign_maximum_threshold(data_with_level_thresholds)

        with open(updated_json, 'w') as file:
            json.dump(data_with_final_thresholds, file, indent=4)
        print(f"Thresholds added and saved: {updated_json}")

        if current_row_count == previous_row_count:
            print("Row count stabilized. Exiting loop.")
            break
        previous_row_count = current_row_count
        # Prepare for next iteration
        input_path = updated_json
        iteration += 1

    print(f"### Round {round} Completed Successfully ###")
    iteration = 0
    round += 1
    output_json = os.path.join(output_dir, f"cpc_abstract_round{round}_iter{iteration + 1}.json")
    excel_file = os.path.join(output_dir, f"cpc_abstract_round{round}_iter{iteration + 1}.xlsx")
    updated_json = os.path.join(output_dir, f"cpc_abstract_round{round}_iter{iteration + 1}_updated.json")
    data = data_with_final_thresholds
    whole_data = data_with_final_thresholds
    # Process Level
    prompt_template = prompts_lvl.PROMPT_TEMPLATES["merge_decision"]
    gen_abstract_cpc_lvl.process_level(whole_data, data, is_top_level=True, prompt_template=prompt_template)
    gen_abstract_cpc_lvl.merge_single_child_nodes(whole_data, is_top_level=True)
    with open(output_json, 'w') as output_file:
        json.dump(data, output_file, indent=4)
    print(f"Processed Level and saved: {output_json}")

    # Step: Visualization
    rows = plot_abstract.process_hierarchy(data)
    df = pd.DataFrame(rows)
    df.to_excel(excel_file, index=False)
    print(f"Visualization saved: {excel_file}")

    # Step 4.3: Add Thresholds
    data_with_sibling_thresholds = add_thresholds_level_sibling_based.add_thresholds_sibling_based(data, z_threshold= z_th)
    data_with_level_thresholds = add_thresholds_level_sibling_based.add_thresholds_level_based(data_with_sibling_thresholds, z_threshold= z_th)
    data_with_final_thresholds = add_thresholds_level_sibling_based.assign_maximum_threshold(data_with_level_thresholds)

    with open(updated_json, 'w') as file:
        json.dump(data_with_final_thresholds, file, indent=4)
    print(f"Thresholds added and saved: {updated_json}")

    input_path = updated_json
print("subjective ending condition is satisfied!")


    

