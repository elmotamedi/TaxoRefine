# prompts.py

PROMPT_TEMPLATES = {
    "decision_on_meta_characteristics":"""
    Your task is to refine a taxonomy of innovations, focusing on <knowledge fields> as the meta-characteristic.
    Based on your evaluation, you should decide to:
    - Retain the category if it aligns with the meta-characteristic.  
    - Remove the category if it does not align.  

    You will receive:
    - The <parent label> of the candidate (if it exists)
    - The <candidate label>
    - A list of <sibling labels>

    ### Output Format
    - If you decide to retain the group, respond with a text 'None'.

    - If you decide to remove the group, respond with the text 'Remove'.

    **Output Requirements:**
    - Do not include any additional explanations or text.

    ### Input Information
    Parent Label: {parent_label}
    Candidate Label: {candidate_label}
    Sibling Labels: {sibling_labels}
    Sibling codes: {sibling_codes}
    """,

    "representative_label_based_on_meta_characteristics":"""
    Your task is to refine a taxonomy of innovations, focusing on <knowledge fields> as the meta-characteristic.
    Your goal is to propose a representative label for a given category that aligns with the defined meta-characteristic. 
    If you decide that the current label is appropriate, you can return the current label as your proposed label. 
    If you decide that the current label is appropriate but the current label is longer than 15 words, still propose
    a shorter label which is up to 15 words

    You will receive: 
    Category for which you have to propose a label
    - Candidate label: {candidate_label}
    - Sibling label: {sibling_labels}
    The categories are under a parent class:
    - Parent Label: {parent_label} ( if the classes are in the first level of hierarchy the parent label will not be provided.)



    Suggest a representative label for this category and not include the parent name in the label. The label should:
    - Be up to 15 words long.
    - Focus only on the specific category itself, without including or referencing the parent name or any hierarchical structure.
    - Do not used <,> in the proposed label

    ### Output Format
    Return the result in the following format:
    - If the proposed label is a new suggestion: `True, <label>`
    - If the proposed label is the same as the current label: `False, <label>`

    Output only the suggested label without any additional explanations.


    """

    # Additional templates 
}