import numpy as np
import pickle

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import random
import os
import json

from typing import Dict, List, Tuple, Any
from app.chatbot.utils import extract_user_facts, extract_user_preferences, generate_workout_plan, \
    get_recommendation, calculate_bmi, get_bmi_category, request_for_data, check_if_user_data_exists, match_exercise
from app.db.crud import get_user_facts, save_user_facts, save_user_preferences, save_message, get_workout_preferences
from app.db.models import User
from sqlalchemy.orm import Session


class ChatbotResources:
    def __init__(self):
        self.sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.X = None
        self.label_encoder = None
        self.responses_dict = None
        self.exercise_sentences = None
        self.exercise_embeddings = None
        self.exercise_lookup = None
        self.wiki_sentences = None
        self.wiki_embeddings = None

    def load_resources(self):
        os.chdir('app/chatbot')

        # Load trained SBERT embeddings, label encoder, and responses
        with open("data/sbert_embeddings.pkl", "rb") as f:
            self.X = pickle.load(f)

        with open("data/label_encoder.pkl", "rb") as f:
            self.label_encoder = pickle.load(f)

        with open("data/responses_dict.pkl", "rb") as f:
            self.responses_dict = pickle.load(f)

        with open("data/exercise_sentences.json", "r") as f:
            self.exercise_sentences = json.load(f)

        with open("data/exercise_embeddings.pkl", "rb") as f:
            self.exercise_embeddings = pickle.load(f)

        with open("data/exercise_lookup.pkl", "rb") as f:
            self.exercise_lookup = pickle.load(f)

        with open("data/wiki_sentences.json", "r") as f:
            self.wiki_sentences = json.load(f)

        with open("data/wiki_embeddings.pkl", "rb") as f:
            self.wiki_embeddings = pickle.load(f)


class ResponseGenerator:
    RESPONSE_TEMPLATES = {
        "bmi": [
            "Based on your height of {height} and weight of {weight}, your BMI is {bmi} You are currently {category}. "
            "For your goal to {goal}, I'd recommend {recommendation}.",

            "I see you're {height} tall and weigh {weight}. With your goal to {goal}, "
            "you should focus on {recommendation}."
        ],
        "workout_plan": [
            "Since you prefer {workout_prefs} and hit the gym on {gym_days},\n"
            "here's your customized plan: {plan}",

            "Your ideal workout plan for {gym_days}, preferring {workout_prefs}:\n{plan}"
        ],
        "diet": [
            "For your {goal} goal, considering you prefer {diet_prefs}, "
            "try this: {diet_plan}",

            "Your personalized meal plan (aligned with your {diet_prefs} preferences):\n{meal_ideas}"
        ]
    }

    def __init__(self, resources: ChatbotResources):
        self.resources = resources

    def generate_bmi_response(self, user_facts: Dict[str, Any]) -> str:
        if not check_if_user_data_exists(user_facts):
            return request_for_data()

        bmi = calculate_bmi(float(user_facts['weight']), float(user_facts['height']))
        recommendation = get_recommendation(user_facts['goal'], bmi)
        category = get_bmi_category(bmi)
        return random.choice(self.RESPONSE_TEMPLATES["bmi"]).format(
            height=user_facts['height'],
            weight=user_facts['weight'],
            bmi=round(bmi, 1),
            goal=user_facts['goal'],
            recommendation=recommendation,
            category=category
        )

    def generate_workout_plan_response(self, user_facts: Dict[str, Any], workout_prefs: List[Dict[str, str]]) -> str:

        if not check_if_user_data_exists(user_facts, True):
            return request_for_data()

        liked_workouts = [
            pref['activity']
            for pref in workout_prefs
            if pref['preference'] == 'like'
        ]

        plan = generate_workout_plan(
            user_facts['gym_days'],
            user_facts['goal']
        )

        return random.choice(self.RESPONSE_TEMPLATES["workout_plan"]).format(
            workout_prefs=", ".join(liked_workouts),
            gym_days=user_facts['gym_days'],
            plan=plan
        )

    def generate_exercise_response(self, user_input: str) -> str:
        matched_exercise, score = match_exercise(
            user_input,
            self.resources.sbert_model,
            self.resources.exercise_embeddings,
            self.resources.exercise_lookup
        )

        if score <= 0.6:
            return self.generate_wiki_response(user_input)

        if any(phrase in user_input.lower() for phrase in
               ["muscle", "which muscle", "target muscle", "muscles targeted", "works on which muscles",
                "muscle group", "focuses on which muscles", "muscle groups involved", "primary muscles"]):
            return (f"The exercise focuses on the following muscles: "
                    f"{', '.join(matched_exercise['primaryMuscles'])}.")

        if any(phrase in user_input.lower() for phrase in
               ["instruction", "how to perform", "how to do", "steps for", "guide for", "how do i", "instructions for",
                "can you explain how to"]):
            return f"Here are the instructions for the exercise: \n" + "\n".join(
                matched_exercise['instructions'])

        return (f"**{matched_exercise['name']}** targets your **{', '.join(matched_exercise['primaryMuscles'])}**.\n"
                f"Here's how to do it:\n" +
                "\n".join([f"{i + 1}. {step}" for i, step in enumerate(matched_exercise['instructions'])])
                )

    def generate_wiki_response(self, user_input: str) -> str:
        query_embedding = self.resources.sbert_model.encode([user_input])[0].reshape(1, -1)
        similarities = cosine_similarity(query_embedding, self.resources.wiki_embeddings)[0]
        top_idx = np.argmax(similarities)

        if similarities[top_idx] > 0.4:
            return f"Here’s what I found: {self.resources.wiki_sentences[top_idx]}"

        return random.choice(self.resources.responses_dict.get("default", ["I'm not sure how to respond."]))


class FitnessChatbot:
    """Main chatbot class handling conversation flow"""

    def __init__(self):
        self.resources = ChatbotResources()
        self.resources.load_resources()
        self.response_generator = ResponseGenerator(self.resources)

    def get_similar_response(self, user_input: str, user: User, conversation_id: int, db: Session) -> Tuple[str, int]:
        self._save_user_message(user.id, conversation_id, user_input, db)

        # Extract and save preferences if any
        preferences = extract_user_preferences(user_input)
        if preferences:
            save_user_preferences(user.id, preferences, db)
            response = self._format_preferences_response(preferences)
            return self._finalize_response(user.id, conversation_id, response, db)

        # Extract and save facts if any
        facts = extract_user_facts(user_input)
        if facts:
            save_user_facts(user.id, facts, db)
            response = self._format_facts_response(facts)
            return self._finalize_response(user.id, conversation_id, response, db)

        # Retrieve stored user data
        user_facts = get_user_facts(user.id, db)
        workout_prefs = get_workout_preferences(user.id, db)

        # Generate context-aware response
        input_embedding = self.resources.sbert_model.encode([user_input.lower()], convert_to_tensor=True).cpu().numpy()
        similarities = cosine_similarity(input_embedding, self.resources.X)[0]

        # Find the best match
        best_match_index = np.argmax(similarities)
        confidence = similarities[best_match_index]
        predicted_label = self.resources.label_encoder.classes_[best_match_index]

        if confidence > 0.6:
            if predicted_label == "bmi":
                response = self.response_generator.generate_bmi_response(user_facts)

            elif predicted_label == "workout_plan":
                response = self.response_generator.generate_workout_plan_response(user_facts, workout_prefs)

            else:
                # Fallback
                generic_response = random.choice(self.resources.responses_dict[predicted_label])
                response = f"{user_facts.get('name', 'There')}, {generic_response.lower()}"

        else:
            response = self.response_generator.generate_exercise_response(user_input)

        self._finalize_response(user.id, conversation_id, response, db)
        return response, conversation_id

    def _save_user_message(self, user_id: int, conversation_id: int, message: str, db: Session):
        """Save user message to database"""
        save_message(user_id, conversation_id, message, is_bot=False, db=db)

    def _format_preferences_response(self, preferences: List[Dict[str, str]]):
        cleaned_preferences = [pref['value'] for pref in preferences]
        return f"I captured your preferences: {', '.join(cleaned_preferences)}"

    def _format_facts_response(self, facts: Dict[str, Any]) -> str:
        response = "Thanks! I've captured the following details you shared with me:"
        if 'weight' in facts:
            response += f"\n- Weight: {facts['weight']} kg"
        if 'height' in facts:
            response += f"\n- Height: {facts['height']} cm"
        if 'goal' in facts:
            response += f"\n- Goal: {facts['goal']}"
        if 'gym_days' in facts:
            response += f"\n- Gym Days: {', '.join(facts['gym_days'])}"
        return response

    def _finalize_response(self, user_id: int, conversation_id: int, response: str, db: Session):
        save_message(user_id, conversation_id, response, is_bot=True, db=db)
        return response, conversation_id


chatbot_instance = FitnessChatbot()