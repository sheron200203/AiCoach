import numpy as np
import pickle
from fastapi import HTTPException
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
import random
import os
from starlette import status

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


def get_similar_response(user_input, user: User,conversation_id: int, db: Session):
    save_message(user.id, conversation_id, user_input, False, db)

    input_embedding = sbert_model.encode([user_input.lower()], convert_to_tensor=True).cpu().numpy()
    similarities = cosine_similarity(input_embedding, X)[0]

    # Find the best match
    best_match_index = np.argmax(similarities)
    confidence = similarities[best_match_index]
    predicted_label = label_encoder.classes_[best_match_index]

    if confidence > 0.3:
        if predicted_label == "bmi":
            response = user.username

        elif predicted_label == "workout_plan":
            response = "Please log in to get a plan."

        else:
            response = random.choice(responses_dict[predicted_label])

    else:
        response = "I'm not sure what you mean. Can you rephrase?"

    save_message(user.id, conversation_id, response, False, db)

    return response


# def get_user_bmi(user: User, db: Session):
#     user_data = db.query(User).filter(User.id == user.id).first()
#     if user_data:
#         weight = user_data.weight
#         height = user_data.height
#         bmi = weight / (height ** 2)
#         return round(bmi, 2)
#     else:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User data not found")