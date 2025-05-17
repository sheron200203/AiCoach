# 🧠 AI Fitness Coach Chatbot (FastAPI + SBERT)

A smart, personalized fitness chatbot built using **FastAPI** and **SBERT** (Sentence-BERT). It provides users with accurate workout plans, dietary suggestions, and fitness advice through a **hybrid NLP + rule-based system**.

---

## 🚀 Features

### 🧠 Natural Language Processing (NLP)

- **SBERT-Based Intent Detection**
  - Uses `all-MiniLM-L6-v2` model to convert user inputs into vector embeddings.
  - Matches inputs to intents using cosine similarity.

- **Context-Aware Classification**
  - Considers user profile and dialogue history for intent prediction.

- **Semantic Fallback Search**
  - Uses a Wikipedia-style corpus with SBERT embeddings when no high-confidence intent match is found.

---

### 🔧 Rule-Based Logic

- **Regex & Keyword Matching**
  - Identifies key phrases like “register” or “sign up” to trigger preset responses.

- **Hardcoded Templates**
  - Predefined response templates with dynamic slot-filling: `{name}`, `{goal}`, `{weight}`, etc.

- **Exercise-Specific Logic**
  - Determines whether the query asks about *instructions* or *target muscles*, using semantic similarity and keyword cues.

---

### 📊 Personalized Data Extraction

- **User Facts**
  - Extracts fitness facts (e.g. weight, height, goal) using regex, spaCy, and rule-based patterns.
  - Stored in `user_facts` table for persistent personalization.

- **User Preferences**
  - Detects likes/dislikes from messages using:
    - spaCy noun chunking
    - Sentiment detection
    - Zero-shot classification (`facebook/bart-large-mnli`)
  - Categories: `food`, `sports`, `cardio exercises`

---

### 🧠 Hybrid Intelligence Engine

- Combines **SBERT-based semantic reasoning** with **rule-based pattern matching**.
- Robust handling of both structured queries (e.g., “Calculate my BMI”) and free-text questions (e.g., “How do I do deadlifts?”).

---

### 🔐 JWT Authentication System
This project uses a robust JWT (JSON Web Token) based authentication system to securely manage user sessions. The setup supports access and refresh token logic, with all critical API routes protected by authentication middleware.

- **✅ Key Features**:
  - Access Token: Short-lived (expires in 30 minutes).
  - Refresh Token: Used to generate a new access token when the current one expires.
  - Secure Cookie Storage: Tokens are stored in HTTP-only cookies to prevent XSS attacks.
  - Protected Routes: All sensitive routes require valid JWT tokens for access.

- **🔁 Token Refresh Logic**
  - The frontend automatically refreshes tokens using Axios interceptors:
  - On receiving a 401 Unauthorized, the interceptor calls /refresh.
  - If the refresh token is valid, a new access token is issued.
  - The original request is retried with the new token.
  - If the refresh token is invalid/expired, the user is logged out.

- **🛡 How Route Protection Works**:
  - A custom get_current_user dependency is used in FastAPI.
  - It verifies the access token from cookies before processing any request.
  - If verification fails, a 401 response is returned immediately.

- **Key end-points**:
  ```bash
  POST /auth/token              -> Authenticates user and issues tokens
  POST /auth/refresh            -> Issues a new access token
  POST /auth/logout             -> Revokes tokens and clears cookies
---

### 💾 Persistent Storage (SQL + File-Based)

- **Database**: MySQL (via XAMPP) + SQLAlchemy ORM  
  Tables include: `users`, `user_facts`, `user_preferences`, `message_history`, `conversations`.

- **Static Files**: `.json` and `.pkl`  
  - Exercise dataset  
  - Precomputed SBERT embeddings  
  - Wikipedia-style fitness knowledge

---

## 📁 Tech Stack

| Layer        | Tech                                  |
|--------------|---------------------------------------|
| Backend      | FastAPI                               |
| NLP Models   | SBERT, spaCy, HuggingFace Transformers|
| Database     | MySQL + SQLAlchemy                    |
| Embeddings   | Sentence-BERT (MiniLM-L6-v2)          |
| Knowledge Base | Wikipedia-style corpus + exercises.json |

---

## 🧪 Setup Instructions

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/ai-fitness-coach.git
cd ai-fitness-coach

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run FastAPI server
uvicorn app.main:app --reload
```
- ✅ Ensure MySQL is running locally (e.g., via XAMPP).
 - 🔐 Update DB credentials in .env or your settings file.

---

## 🤝 Contributions 
  - PRs and feedback welcome! Feel free to open issues or suggest features.
