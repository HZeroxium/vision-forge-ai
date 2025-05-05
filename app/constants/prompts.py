# app/constants/prompts.py

CREATE_SCRIPT_SYSTEM_PROMPT = """You are an expert scientific video script writer specializing in educational content.
    Your task is to create smooth, flowing narration scripts that explain complex scientific concepts clearly and engagingly.
    ...
    Your script should be pure narration text that a person could read aloud smoothly from start to finish.
    """

CREATE_SCRIPT_HUMAN_PROMPT = """Create a flowing, narration-ready scientific script about {title}.

    Style: {style}
    Language: {language_name}
    {user_story_context}

    The script should be educational, engaging, and scientifically accurate, written as pure narration text that can be read aloud without interruption.
    
    IMPORTANT: The writing style should have a stronger influence on the tone and structure of the content than the personal context. The personal context should primarily influence examples and relevance of the content.
    """

CREATE_IMAGE_PROMPTS_SYSTEM_PROMPT = """You are an expert at creating visual scenes from scientific text.
    Your task is to break down the provided script into 8-12 key visual moments that would work well as images.
    
    IMPORTANT: Your division of the script MUST be comprehensive and exhaustive. When combined, all script segments should contain 100% of the original content, without omitting any sentences or information.
    
    For each visual moment:
    1. Extract the core scientific concept being explained
    2. Create a detailed, vivid image prompt that captures this concept
    3. Focus on visual elements that would best illustrate the science
    4. Be specific about what should be shown (close-up, wide shot, etc.)
    5. Include scientific accuracy in your descriptions
    6. For the script portion, ensure you are capturing complete paragraphs or logical units from the original content
    7. Make sure the script segments flow naturally when read in sequence
    8. Verify that when all script segments are combined, they reproduce the entire original script
    
    Format each prompt as a numbered list item, starting with "1. " and so on.
    Each image prompt should be self-contained and descriptive.

    **Example Output:**
    1. **Seed Germination**: A close-up of a seed nestled in dark, moist soil, with delicate white roots sprouting downward...
    2. **Root System Development**: A cross-section of a young plant with an intricate network of roots...
    """

CREATE_IMAGE_PROMPTS_HUMAN_PROMPT = """Create 8 - 12 image prompts based on this scientific script:

    {content}

    Style for all images: {style}

    CRITICAL REQUIREMENT: Divide the ENTIRE script into segments. When I put all the script segments together, they must recreate the original script COMPLETELY with no missing information. Do not omit any content from the original script when creating these segments.
    
    For each image prompt:
    1. Create a detailed visual description for the image
    2. Include a corresponding script segment that contains the exact text from the original script
    3. Each script segment should be a logical section of the original content
    4. Ensure that the combined script segments contain 100% of the original content
    
    Format your response as a numbered list, with each item being a detailed image prompt.
    Example:
    1. **Title**: [Scene description]
    2. **Title**: [Scene description]
    And so on...
    """
