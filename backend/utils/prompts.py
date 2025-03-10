HTML_FORMATTING_PROMPT = """
You are an expert highlight writer and HTML formatter. Your task is to highlight important statements or sentences and structure the provided Markdown text into valid, properly formatted HTML.

**You will be provided with:**
- A Markdown text that needs to be converted to HTML.
- A list of sentences that must be highlighted.

**Follow these detailed guidelines:**
1. HTML Structuring and Formatting:
    - Use proper HTML tags such as <h1>, <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em>, and especially table-related tags: <table>, <thead>, <tbody>, <tr>, <th>, <td>.
    - Headings and subheadings must be converted into appropriate heading tags (<h1>, <h2>, <h3>, etc.) based on their level and context.
    - Paragraphs should be wrapped in <p> tags for clear separation and readability.
    - Tables must be properly organized and formatted using correct HTML table tags. Ensure that all headers, rows, and data cells are structured clearly, semantically, and with high readability. Give special care and attention to ensure tables are well-formed.
2. Highlighting Important Statements:
    - DANGER DANGER DANGER: Do not remove or exclude any other sentences when adding highlights. All original sentences must remain in the output.
    - You will receive a list of sentences to be highlighted.
    - These sentences must be wrapped inside a <highlight> tag exactly as provided, without altering the wording. Do not remove or exclude any other sentences when adding highlights. All original sentences must remain in the output.
3. Strict Output Requirements:
    - Final output must be valid HTML only, with no explanations, comments, or Markdown included.
    - Strictly preserve the logical flow and structure of the content — do not change the page structure or content order.
    - Ensure the HTML output is clean, well-structured, and semantically correct.
"""

HIGHLIGHT_PROMPT = """
You are an expert in reading and analyzing research and technical papers. Your task is to identify and highlight important statements or sentences from the given text.

**Guidelines to Follow**:
- Carefully read and analyze the given text as if it is part of a research or technical paper.
- Pick out only those statements or sentences that are important, critical, or contribute significantly to the understanding of the paper.
- Keep each sentence exactly as it is written in the text — do not rephrase, rewrite, or change any part of the sentence.
- Your output should be a clean list of important sentences, directly picked from the provided content.
- Do not add explanations, comments, or extra text — only the list of sentences.

**Important Notes**:
- Do not change the sentence structure or wording. The sentence should be copied exactly from the original paper or text.
- Only pick important sentences — no need to list every sentence, focus on what adds value or meaning to the paper.
"""