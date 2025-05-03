import string
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import random
import ast
from typing import Union, List

import spacy
import re
from transformers import pipeline

# Load once globally
nlp = spacy.load("en_core_web_sm")
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


def extract_user_preferences(message: str):
    noise_words = {"lot", "something", "things", "thing", "time", "do"}
    negative_phrases = ["don't like", "do not like", "hate", "dislike", "can't stand"]
    positive_phrases = ["like", "love", "prefer", "enjoy"]
    contrast_words = ["but", "however", "although", "except"]

    candidate_labels = [
        "exercise",
        "cardio exercise",
        "fitness class",
        "sports",
        "food",
        "other"
    ]

    def detect_sentiment(clause):
        text = clause.lower()
        for phrase in negative_phrases:
            if phrase in text:
                return "dislike"
        for phrase in positive_phrases:
            if phrase in text:
                return "like"
        return None

    def clean_text(text):
        return re.sub(r"[^\w\s]", "", text).strip().lower()

    def process_clause(clause, sentiment):
        doc = nlp(clause)
        results = []

        # Handle noun chunks
        seen = set()
        for chunk in doc.noun_chunks:
            chunk_text = clean_text(chunk.text)
            seen.add(chunk_text)
            if (
                    chunk.root.pos_ in ["NOUN", "PROPN"]
                    and chunk_text not in noise_words
                    and not any(phrase in chunk_text for phrase in positive_phrases + negative_phrases)
            ):
                classification = classifier(chunk_text, candidate_labels, multi_label=False)
                category = classification["labels"][0]

                results.append({
                    "value": chunk_text,
                    "sentiment": sentiment,
                    "category": category,
                    "type": "workout" if "exercise" in category or "fitness" in category or "sports" in category else "food"
                })

        # Handle verbs (including gerunds like "running") separately
        for token in doc:
            if (
                    token.pos_ == "VERB"
                    and token.lemma_ not in seen
                    and token.text.lower() not in noise_words
                    and not any(phrase in token.text.lower()  for phrase in positive_phrases + negative_phrases)
            ):
                token_text = clean_text(token.text)
                if token_text and token_text not in seen:
                    classification = classifier(token_text, candidate_labels, multi_label=False)
                    category = classification["labels"][0]
                    results.append({
                        "value": token_text,
                        "sentiment": sentiment,
                        "category": category,
                        "type": "workout" if "exercise" in category or "fitness" in category or "sports" in category else "food"
                    })

        return results

    results = []

    # Split on contrast words to isolate sentiment clauses
    contrast_split = re.split(rf"\b({'|'.join(contrast_words)})\b", message, flags=re.IGNORECASE)

    # Combine into meaningful clauses
    clauses = []
    current_clause = ""
    for segment in contrast_split:
        if segment.strip().lower() in contrast_words:
            if current_clause:
                clauses.append(current_clause.strip())
            current_clause = ""
        else:
            current_clause += " " + segment
    if current_clause:
        clauses.append(current_clause.strip())

    # Analyze each clause
    for clause in clauses:
        sentiment = detect_sentiment(clause)
        if sentiment:
            results.extend(process_clause(clause, sentiment))

    return results


def extract_user_facts(message: str):
    doc = nlp(message)
    facts = {}

    text = message.lower()

    weight_match = re.search(
        r"(?:\bweight is\b|\bi weigh\b|\bweigh\b|weight:)?\s*(\d{2,3})\s*(?:kg|kilograms)\b", text)
    if weight_match:
        weight = int(weight_match.group(1))
        if 30 <= weight <= 200:
            facts["weight"] = weight

    height_match = re.search(
        r"(?:\bheight\b\s*(?:is|:)?|\bi am\b|\bi'm\b)?\s*(\d{3})\s*(?:cm|centimeters)\b", text, re.IGNORECASE)
    if height_match:
        height = int(height_match.group(1))
        if 100 <= height <= 250:
            facts["height"] = height

    for sent in doc.sents:
        if "goal" in sent.text.lower():
            match = re.search(r"goal(?: is|:)?\s*(.+)", sent.text, re.IGNORECASE)
            if match:
                facts["goal"] = match.group(1).strip(". ")

    days = []
    for token in doc:
        if token.text.lower() in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            days.append(token.text.capitalize())
    if days:
        facts["gym_days"] = days

    return facts


def generate_title_from_message(message: str) -> str:
    return message[:40] + "..." if len(message) > 40 else message


def calculate_bmi(weight: float, height: float) -> float:
    height = height / 100
    return weight / (height ** 2)


def get_bmi_category(bmi: float) -> string:
    bmi_category = (
        "underweight" if bmi < 18.5 else
        "normal" if bmi < 25 else
        "overweight" if bmi < 30 else
        "obese"
    )
    return bmi_category


def get_recommendation(goal: str, bmi: float) -> str:
    recommendations = {
        "lose weight": {
            "underweight": "a balanced diet with strength training to build healthy muscle",
            "normal": "moderate calorie deficit with cardio and resistance training",
            "overweight": "a calorie-controlled diet with regular cardio exercise",
            "obese": "gradual weight loss through diet modification and low-impact exercise"
        },
        "gain muscle": {
            "underweight": "calorie surplus with strength training 3-5x/week",
            "normal": "slight calorie surplus with progressive overload training",
            "overweight": "body recomposition approach with strength training",
            "obese": "focus on strength training while maintaining slight calorie deficit"
        }
    }

    bmi_category = get_bmi_category(bmi)

    return recommendations.get(goal, {}).get(bmi_category, "regular exercise and balanced nutrition")


def generate_workout_plan(
        days: Union[str, List[str]],
        goal: str,
        experience: str = "beginner"
) -> str:
    """
    Generates a workout plan for dynamic days input
    - Handles both string and list inputs
    - Returns formatted plan
    """

    workout_days = []

    if isinstance(days, str):
        try:
            workout_days = ast.literal_eval(days)
            if not isinstance(workout_days, list):
                workout_days = days.split(',')
        except:
            workout_days = days.split(',')

    # Ensure we have a clean list of days
    workout_days = [day.strip(" []'\"") for day in workout_days if day.strip()]
    if not workout_days:
        workout_days = ["Monday", "Wednesday", "Friday"]  # Default

    # 2. EXERCISE SELECTION
    exercises = {
        "build muscle": {
            "beginner": ["Push-ups", "Dumbbell rows", "Bodyweight squats"],
            "intermediate": ["Bench press", "Deadlifts", "Pull-ups"],
            "advanced": ["Weighted pull-ups", "Barbell squats", "Overhead press"]
        },
        "lose fat": {
            "beginner": ["Jumping jacks", "Bodyweight circuits", "Walking lunges"],
            "intermediate": ["Kettlebell swings", "Box jumps", "Battle ropes"],
            "advanced": ["Sprint intervals", "Complex lifts", "HIIT circuits"]
        }
    }

    # Load appropriate exercises
    goal = goal.lower()
    workout_type = exercises.get(goal, exercises["build muscle"])
    daily_exercises = workout_type.get(experience, workout_type["beginner"])

    # 3. PLAN GENERATION
    plan = []
    for day in workout_days:
        selected = random.sample(daily_exercises, min(3, len(daily_exercises)))
        plan.append(f"{day.strip()}: {', '.join(selected)}")

    return f"\n \n Your {len(workout_days)}-day '{goal}' plan:\n \n" + "\n".join(plan)


def check_if_user_data_exists(user_facts, include_workout_days: bool = False):
    required_keys = ['weight', 'height', 'goal']

    if include_workout_days:
        required_keys.append('gym_days')

    return all(key in user_facts and user_facts[key] is not None for key in required_keys)


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


def match_exercise(query: str, model, embeddings, lookup):
    query_embedding = model.encode([query])[0].reshape(1, -1)
    scores = cosine_similarity(query_embedding, embeddings)[0]
    top_idx = np.argmax(scores)
    matched_exercise = lookup[top_idx]

    return matched_exercise, scores[top_idx]


def request_for_data():
    prompt = (
        "It looks like I don't have your height, weight, fitness goal, or gym days stored yet. \n"
        "Please provide these details, and I'll store them to offer you customized solutions!"
    )
    return prompt