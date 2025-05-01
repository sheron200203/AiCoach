import re


def clean_wiki_text(text):
    text = re.sub(r'\[\d+\]', '', text)  #[70]
    text = re.sub(r'\{\{.*?\}\}', '', text)  # {{Infobox}}
    text = re.sub(r'\[\[.*?\]\]', '', text)  # [[Link]]

    text = re.sub(r'\[ edit ]', '', text)
    # HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text
