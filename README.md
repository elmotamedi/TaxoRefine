# Semi-Automatic Taxonomy Refinement Using LLMs

This repository contains the implementation of the method described in the paper:

**"TITLE OF YOUR PAPER"**  
_Author(s): Your Name, Collaborators_  
Submitted to: *[Journal/Conference Name]*  

---

## Overview

This project proposes a **semi-automatic method for refining hierarchical taxonomies** by:

- Starting from a fine-grained, existing taxonomy
- Identifying small or low-support classes as merge candidates
- Using **LLMs (e.g., GPT-4)** to evaluate semantic similarity and propose group merges
- Supporting **optional expert review** to validate and adjust LLM decisions

We validate the approach by abstracting the **Cooperative Patent Classification (CPC)** schema and applying the refined taxonomy to a **patent classification** task.

---

## Project Structure

## Requirements

Create a virtual environment and install dependencies:

### 🖥️ On Windows:

py -m venv .myenv
.myenv\Scripts\activate
pip install -r requirements.txt

### 💻 On macOS/Linux:

python3 -m venv .myenv
source .myenv/bin/activate
pip install -r requirements.txt

### Install the dependencies:
Using either of the following commands:
pip3 install -r requirements.txt
or
python -m pip install -r requirements.txt

## How to Run the Experiment

Follow these steps to reproduce the taxonomy refinement process:

1. **Set Merge Thresholds**
   - Run:  
     ```bash
     python init_taxonomy/set_threshold/update_threshold.py
     ```
   - **Input:** `data/cpc/label_count.json`  
   - **Output:** `output/cpc/abstract_cpc/label_count_updated.json`

2. **Add Parent Pointers**
   - Run:  
     ```bash
     python init_taxonomy/add_parent/add_pointers_to_parents.py
     ```
   - **Input:** `output/cpc/abstract_cpc/label_count_updated.json`  
   - **Output:** `label_count_updated_parents.json`

3. **Refine Taxonomy with Meta-Perspective**
   - Run:  
     ```bash
     python init_taxonomy/refine_with_meta/refine_taxonomy_perspective.py
     ```
   - **Input:** `label_count_updated_parents.json`  
   - **Output:** `output/cpc/abstract_cpc/cpc_abstract_meta_refined_relevants.json`

4. **Run Main Pipeline**
   - Run:  
     ```bash
     python main.py
     ```
   - **Input:** `cpc_abstract_meta_refined_relevants.json`  
   - **Output:** abstracted taxonomies in each iteration in output/cpc/abstract_cpc/


## 📚 Citation
If you use this code in your work, please cite:
