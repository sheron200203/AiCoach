import json
import pathlib

import nltk
import numpy as np
import pickle

from newspaper import Article
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import LabelEncoder

from app.chatbot.utils import clean_wiki_text

nltk.download('punkt')
# Load dataset
with open("data/data.json", "r") as file:
    data = json.load(file)

# Initialize SBERT model
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

# Prepare training data
patterns = []
tags = []
responses_dict = {}

for intent in data["intents"]:
    for pattern in intent["patterns"]:
        patterns.append(pattern.lower())
        tags.append(intent["tag"])

    responses_dict[intent["tag"]] = intent["responses"]

# Convert text to embeddings
X = sbert_model.encode(patterns)  # Convert patterns to embeddings
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(tags)  # Encode intent labels

# Ensure embeddings and labels are correctly aligned
unique_tags = list(label_encoder.classes_)
tag_to_embeddings = {tag: [] for tag in unique_tags}

for i, tag in enumerate(tags):
    tag_to_embeddings[tag].append(X[i])

# Compute the mean embedding per intent
final_embeddings = []
final_labels = []

for tag, embeddings in tag_to_embeddings.items():
    mean_embedding = np.mean(embeddings, axis=0)  # Compute the average embedding
    final_embeddings.append(mean_embedding)
    final_labels.append(tag)

final_embeddings = np.array(final_embeddings)

# Save embeddings, encoder, and responses
with open("data/sbert_embeddings.pkl", "wb") as f:
    pickle.dump(final_embeddings, f)

with open("data/label_encoder.pkl", "wb") as f:
    pickle.dump(label_encoder, f)

with open("data/responses_dict.pkl", "wb") as f:
    pickle.dump(responses_dict, f)


def get_sentences_from_url(url, cache_path):
    CACHE = pathlib.Path(cache_path)
    if CACHE.exists():
        return json.loads(CACHE.read_text())

    article = Article(url)
    article.download()
    article.parse()
    raw_text = article.text

    # Clean the raw text before processing
    cleaned_text = clean_wiki_text(raw_text)

    # Tokenize into sentences using NLTK
    sentences = nltk.sent_tokenize(cleaned_text)

    # Save sentences to cache
    CACHE.write_text(json.dumps(sentences, ensure_ascii=False, indent=2))
    return sentences


# Load fitness knowledge base sentences
fitness_url = "https://en.wikipedia.org/wiki/Strength_training"
wiki_sentences = get_sentences_from_url(fitness_url, "data/fitness_wiki.json")

# Compute embeddings for the KB
wiki_embeddings = sbert_model.encode(wiki_sentences)

# Save the KB sentences and their embeddings
with open("data/wiki_sentences.json", "w") as f:
    json.dump(wiki_sentences, f, ensure_ascii=False, indent=2)

with open("data/wiki_embeddings.pkl", "wb") as f:
    pickle.dump(wiki_embeddings, f)

print("AI Training completed")