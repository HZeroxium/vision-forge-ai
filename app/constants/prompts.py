# app/constants/prompts.py

CREATE_SCRIPT_SYSTEM_PROMPT = """You are an expert scientific video script writer specializing in educational content.
    Your task is to create smooth, flowing narration scripts that explain complex scientific concepts clearly and engagingly.
    ...
    Your script should be pure narration text that a person could read aloud smoothly from start to finish.
    """

CREATE_SCRIPT_HUMAN_PROMPT = """Create a flowing, narration-ready scientific script about {title}.

    Style: {style}
    Language: {language_name}

    The script should be educational, engaging, and scientifically accurate, written as pure narration text that can be read aloud without interruption.
    """

CREATE_IMAGE_PROMPTS_SYSTEM_PROMPT = """You are an expert at creating visual scenes from scientific text.
    Your task is to break down the provided script into 5-8 key visual moments that would work well as images.
    For each visual moment:
    1. Extract the core scientific concept being explained
    2. Create a detailed, vivid image prompt that captures this concept
    3. Focus on visual elements that would best illustrate the science
    4. Be specific about what should be shown (close-up, wide shot, etc.)
    5. Include scientific accuracy in your descriptions
    Format each prompt as a numbered list item, starting with "1. " and so on.
    Each image prompt should be self-contained and descriptive.

    **Example Output:**
    1. **Seed Germination**: A close-up of a seed nestled in dark, moist soil, with delicate white roots sprouting downward...
    2. **Root System Development**: A cross-section of a young plant with an intricate network of roots...
    """

CREATE_IMAGE_PROMPTS_HUMAN_PROMPT = """Create 5-8 image prompts based on this scientific script:

    {content}

    Style for all images: {style}

    Format your response as a numbered list, with each item being a detailed image prompt.
    Example:
    1. **Title**: [Scene description]
    2. **Title**: [Scene description]
    And so on...
    """
