import numpy as np
import pickle

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import random
import os
import json

from app.db.crud import save_message
from app.db.models import User
from sqlalchemy.orm import Session

os.chdir('app/chatbot')

# Load trained SBERT embeddings, label encoder, and responses
with open("data/sbert_embeddings.pkl", "rb") as f:
    X = pickle.load(f)

with open("data/label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)

with open("data/responses_dict.pkl", "rb") as f:
    responses_dict = pickle.load(f)

# Load SBERT model
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')


def get_similar_response(user_input, user: User, conversation_id: int, db: Session):
    save_message(user.id, conversation_id, user_input, is_bot=False, db=db)

    # Generate context-aware response
    input_embedding = sbert_model.encode([user_input.lower()], convert_to_tensor=True).cpu().numpy()
    similarities = cosine_similarity(input_embedding, X)[0]

    # Find the best match
    best_match_index = np.argmax(similarities)
    confidence = similarities[best_match_index]
    predicted_label = label_encoder.classes_[best_match_index]

    if confidence > 0.6:
        if predicted_label == "bmi":
            response = "Here is your BMI"

        elif predicted_label == "workout_plan":
            response = "Here's your workout plan"

        else:
            # Fallback to generic responses with personalization
            generic_response = random.choice(responses_dict[predicted_label])
            response = generic_response

    else:
        with open("data/wiki_sentences.json", "r") as f:
            wiki_sentences = json.load(f)

        with open("data/wiki_embeddings.pkl", "rb") as f:
            wiki_embeddings = pickle.load(f)

        query_embedding = sbert_model.encode([user_input])[0].reshape(1, -1)
        similarities = cosine_similarity(query_embedding, wiki_embeddings)[0]
        top_idx = np.argmax(similarities)

        if similarities[top_idx] > 0.4:
            response = f"Here’s what I found: {wiki_sentences[top_idx]}"
        else:
            response = random.choice(responses_dict.get(predicted_label, ["I'm not sure how to respond."]))

    save_message(user.id, conversation_id, response, is_bot=True, db=db)
    return response
