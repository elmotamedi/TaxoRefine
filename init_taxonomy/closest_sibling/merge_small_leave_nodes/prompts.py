# prompts.py

PROMPT_TEMPLATES = {
    "merge_decision": """
    Your task is to develop a taxonomy of innovations, focusing on <knowledge field> as meta-characteristic.

    ### Criteria for Merging:
    You must merge the candidate category with one of the sibling categories that has:
   - Overlapping knowledge (shared topics or related application areas),
   - Similar meaning, or
   - Closely related subject area.

    You will receive:
    - The <parent label> of the candidate (if it exists)
    - The <candidate label>
    - A list of <sibling labels>
    - A list of <sibling codes>

    ### Output Format
    - The most similar sibling, respond with a valid Python dictionary object, as shown below:
    
    {{"sibling_code": "code_of_closest_sibling ", "sibling_label": "label_of_closest_sibling "}}

    **Output Requirements:**
    - Do not include any additional explanations or text.

    ### Input Information
    Parent Label: {parent_label}
    Candidate Label: {candidate_label}
    Sibling Labels: {sibling_labels}
    Sibling codes: {sibling_codes}
    """,

    
    "representative_label_for_merge": """
    Your task is to develop a taxonomy of knowledge fields, focusing on <section sectors> as meta-characteristic. 
    You have to merge the following categories (i.e., the candidate group and sibling) to create a new, more abstract 
    class in a taxonomy of knowledge fields.

    You will receive: 
    Categories to merge and their corresponding labels
    - Candidate Code: {candidate_code}
    - Candidate label: {candidate_label}
    - Sibling Code: {sibling_code}
    - Sibling label: {sibling_label}
    The categories are under a parent class:
    - Parent Label: {parent_label} ( if the classes are in the first level of hierarchy the parent label will not be provided.)



    Suggest a representative label for this merged category. The label should:
    - Be up to 10 words long.
    - Reflect the combined knowledge of the merged classes.

    Output only the suggested label without any additional explanations.
    """
    # Additional templates 
}