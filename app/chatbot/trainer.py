import json
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import LabelEncoder

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

print("SBERT model training complete! Files saved.")