import os
import pickle
import torch
import pandas as pd
from flask import Blueprint, request, jsonify, current_app
from sentence_transformers import SentenceTransformer, util
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory
from datetime import datetime
import re
import time
import random
from flask_login import current_user
from bson import ObjectId  
from app.tmdb import search_movie, make_card_from_tmdb_obj, tmdb_similar
from app.utils import linear_kernel
from app.recommendation import recommend_from_dataset, recommend_fallback_tmdb

# Set deterministic language detection
DetectorFactory.seed = 0

# Set offline mode to prevent internet requests
os.environ['TRANSFORMERS_OFFLINE'] = '1'

chatbot_bp = Blueprint("chatbot", __name__)

# Load model and data once
try:
    # Try to load from local cache without internet
    model = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
    print("DEBUG: Chatbot model loaded successfully from cache")
except Exception as e:
    print(f"ERROR: Failed to load model from cache: {e}")
    # Fallback to online download
    os.environ['TRANSFORMERS_OFFLINE'] = '0'
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("DEBUG: Chatbot model downloaded successfully")
    except Exception as e2:
        print(f"ERROR: Failed to download model: {e2}")
        model = None

# Initialize variables
questions, answers, qa_embeddings, qa_df = None, None, None, None

try:
    # Load everything from the single pickle file
    with open("chatbot_model/qa_dataset.pkl", 'rb') as f:
        model_data = pickle.load(f)
    
    # Extract components from the single file
    questions = model_data['questions']
    answers = model_data['answers']
    qa_embeddings = model_data['embeddings']
    
    # Create a DataFrame for compatibility with existing code
    qa_df = pd.DataFrame({
        'question': questions,
        'answer': answers
    })
    
    print("DEBUG: QA dataset and embeddings loaded successfully")
    print(f"DEBUG: Loaded {len(questions)} Q&A pairs")
    print(f"DEBUG: Embeddings shape: {qa_embeddings.shape}")
    
except Exception as e:
    print(f"ERROR: Failed to load QA dataset: {e}")
    questions, answers, qa_embeddings, qa_df = None, None, None, None


# Predefined greetings
GREETINGS = {
    "hello": "👋 Hi there! How can I help you with movies today?",
    "hi": "😊 Hello! Looking for a movie recommendation?",
    "hey": "👋 Hey! Ask me about movies, genres, or actors.",
    "how are you": "😃 I'm doing great, thanks! Ready to recommend you some movies 🎬",
    "thanks": "🙏 You're welcome! Happy to help with your movie search.",
    "thank you": "🙏 You're welcome! Happy to help with your movie search."
}

# Fallback responses if model loading fails
FALLBACK_RESPONSES = [
    "I recommend checking out 'Inception' if you like mind-bending thrillers!",
    "Have you seen 'The Shawshank Redemption'? It's a classic!",
    "If you enjoy action movies, 'Mad Max: Fury Road' is fantastic!",
    "For a good laugh, I'd suggest 'Superbad' or 'The Hangover'.",
    "'The Dark Knight' is a must-watch if you haven't seen it yet!",
    "If you're in the mood for something emotional, 'The Pursuit of Happyness' is great.",
    "For sci-fi fans, 'Interstellar' is an amazing experience!",
    "Check out 'Parasite' if you want something thought-provoking and award-winning."
]

RECOMMENDATION_PATTERNS = [
    'recommend', 'suggest', 'what should i watch', 'movies like', 'recommend something like','i want something similar to',
    'similar to', 'good movies', 'best movies', 'what to watch','suggest for me something like',
    'like', 'similar movies', 'suggestion', 'how about', 'what about','i want movies like'
]

def extract_movie_from_query(query):
    """Improved movie name extraction that handles your recommendation system"""
    patterns = [
        r'recommend.*like (.+?)(?:\.|\?|$)', 
        r'suggest.*like (.+?)(?:\.|\?|$)',
        r'movies like (.+?)(?:\.|\?|$)',
        r'similar to (.+?)(?:\.|\?|$)',
        r'like (.+?)(?:\.|\?|$)',
        r'recommendations for (.+?)(?:\.|\?|$)',
        r'suggestions for (.+?)(?:\.|\?|$)',
        r'what about (.+?)(?:\.|\?|$)',
        r'how about (.+?)(?:\.|\?|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            movie_name = match.group(1).strip()
            movie_name = clean_movie_name(movie_name)
            
            # Verify the movie exists in your system
            if verify_movie_exists(movie_name):
                return movie_name
    
    return None

def verify_movie_exists(movie_name):
    """Check if movie exists in either dataset or TMDB"""
    try:
        # Check if in dataset
        from app.utils import df
        if df is not None and movie_name.lower() in set(df["title_clean"].values):
            return True
        
        # Check if in TMDB
        tmdb_result = search_movie(movie_name)
        if tmdb_result:
            return True
            
    except Exception as e:
        print(f"ERROR verifying movie: {e}")
    
    return False

def clean_movie_name(movie_name):
    """Clean movie names for your recommendation system"""
    # Remove common phrases
    remove_phrases = ['the movie', 'the film', 'movie called', 'film called', 'show me','something like','similar to']
    for phrase in remove_phrases:
        movie_name = re.sub(phrase, '', movie_name, flags=re.IGNORECASE)
    
    # Remove trailing punctuation
    movie_name = re.sub(r'[.,!?;:]$', '', movie_name)
    
    # Remove quotes
    movie_name = movie_name.replace('"', '').replace("'", "")
    
    return movie_name.strip()

def get_recommendations_for_movie(movie_name):
    """Get recommendations using your existing system but format for chat"""
    try:
        print(f"DEBUG: Getting recommendations for: {movie_name}")
        
        # First try your dataset-based recommendations
        recommendations = recommend_from_dataset(movie_name, top_n=5, country="US")
        
        if not recommendations:
            # If not found in dataset, try TMDB fallback
            print(f"DEBUG: Movie not in dataset, trying TMDB fallback")
            recommendations = recommend_fallback_tmdb(movie_name, top_n=5, country="US")
        
        if recommendations:
            return format_recommendations_for_chat(recommendations, movie_name)
        else:
            return f"I couldn't find specific recommendations for *{movie_name}*. {get_general_recommendations()}"
            
    except Exception as e:
        print(f"ERROR getting recommendations: {e}")
        return f"🎬 I'm having trouble finding recommendations for *{movie_name}*. {get_general_recommendations()}"

def format_recommendations_for_chat(recommendations, original_movie):
    """Format movie cards into a nice chat response"""
    if not recommendations:
        return f"I couldn't find recommendations for *{original_movie}* 😢"
    
    response = f"🎬 Based on *{original_movie.title()}*, I recommend:\n\n"
    
    for i, movie in enumerate(recommendations, 1):
        title = movie.get('title', 'Unknown Movie')
        year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
        rating = movie.get('vote_average', '')
        overview = movie.get('overview', '')
        
        response += f"**{i}. {title}**"
        if year:
            response += f" ({year})"
        if rating:
            response += f" ⭐ {rating}/10"
        response += "\n"
        
        # Add brief description if available
        if overview and len(overview) > 0:
            brief_overview = overview[:100] + "..." if len(overview) > 100 else overview
            response += f"   *{brief_overview}*\n"
        
        response += "\n"
    
    response += "\nWould you like more details about any of these? 😊"
    return response

def get_recommendations_by_genre(query):
    """Get genre-based recommendations using your system"""
    genre_map = {
        'action': "Action", 'comedy': "Comedy", 'drama': "Drama",
        'horror': "Horror", 'sci-fi': "Science Fiction", 'romantic': "Romance",
        'thriller': "Thriller", 'adventure': "Adventure", 'animation': "Animation"
    }
    
    query_lower = query.lower()
    for keyword, genre in genre_map.items():
        if keyword in query_lower:
            # Use a popular movie in that genre as a seed
            seed_movies = {
                'action': "The Dark Knight",
                'comedy': "Superbad", 
                'drama': "The Shawshank Redemption",
                'horror': "The Shining",
                'sci-fi': "Inception",
                'romantic': "The Notebook",
                'thriller': "Se7en",
                'adventure': "Indiana Jones",
                'animation': "Toy Story"
            }
            
            seed_movie = seed_movies.get(keyword, "The Shawshank Redemption")
            recommendations = recommend_fallback_tmdb(seed_movie, top_n=5, country="US")
            
            if recommendations:
                return format_genre_recommendations(recommendations, genre)
            else:
                return f"🎬 Top {genre} Movies:\n• Check out popular {genre} films on TMDB!\n\nOr try asking for a specific {genre} movie. 😊"
    
    return get_general_recommendations()

def format_genre_recommendations(recommendations, genre):
    """Format genre recommendations for chat"""
    response = f"🎬 Top {genre} Movies:\n\n"
    
    for i, movie in enumerate(recommendations, 1):
        title = movie.get('title', 'Unknown Movie')
        year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
        rating = movie.get('vote_average', '')
        
        response += f"**{i}. {title}**"
        if year:
            response += f" ({year})"
        if rating:
            response += f" ⭐ {rating}/10"
        response += "\n"
    
    return response

def get_general_recommendations():
    """Get general recommendations using popular movies"""
    popular_movies = ["The Dark Knight", "Inception", "The Shawshank Redemption", "Pulp Fiction", "Forrest Gump"]
    
    response = "🎬 Here are some highly recommended movies:\n\n"
    
    for i, movie in enumerate(popular_movies, 1):
        # Get details for each popular movie
        movie_data = search_movie(movie)
        if movie_data:
            title = movie_data.get('title', movie)
            year = movie_data.get('release_date', '')[:4] if movie_data.get('release_date') else ''
            rating = movie_data.get('vote_average', '')
            
            response += f"**{i}. {title}**"
            if year:
                response += f" ({year})"
            if rating:
                response += f" ⭐ {rating}/10"
            response += "\n"
        else:
            response += f"**{i}. {movie}**\n"
    
    response += "\nWant recommendations based on a specific movie or genre? 😊"
    return response


def handle_recommendation_request(query):
    """Handle movie recommendation requests"""
    query_lower = query.lower()
    
    # Extract movie name for "like X" queries
    movie_name = extract_movie_from_query(query)
    
    if movie_name:
        return get_recommendations_for_movie(movie_name)
    elif any(genre in query_lower for genre in ['action', 'comedy', 'drama', 'horror', 'sci-fi', 'romantic', 'thriller', 'adventure', 'animation']):
        return get_recommendations_by_genre(query)
    else:
        return get_general_recommendations()

def save_conversation(user_id, user_message, bot_response):
    """Save conversation to database"""
    try:
        from datetime import datetime
        
        # Make sure the collection exists
        if not hasattr(current_app, 'conversations_col'):
            print("ERROR: conversations_col not found in app")
            return False
        
        print(f"DEBUG: Saving conversation for user {user_id}")
        print(f"DEBUG: User message: {user_message}")
        print(f"DEBUG: Bot response: {bot_response}")
        
        # Get or create today's conversation
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        
        conversation = current_app.conversations_col.find_one({
            "user_id": user_id,
            "created_at": {"$gte": start_of_day}
        })
        
        if conversation:
            print(f"DEBUG: Appending to existing conversation {conversation['_id']}")
            # Append to existing conversation
            result = current_app.conversations_col.update_one(
                {"_id": conversation["_id"]},
                {"$push": {"messages": {
                    "user": user_message,
                    "bot": bot_response,
                    "timestamp": datetime.now()
                }},
                 "$set": {"updated_at": datetime.now()}}
            )
            print(f"DEBUG: Update result - matched: {result.matched_count}, modified: {result.modified_count}")
            
        else:
            print("DEBUG: Creating new conversation")
            # Create new conversation
            conversation_data = {
                "user_id": user_id,
                "messages": [{
                    "user": user_message,
                    "bot": bot_response,
                    "timestamp": datetime.now()
                }],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            result = current_app.conversations_col.insert_one(conversation_data)
            print(f"DEBUG: New conversation created with ID: {result.inserted_id}")
            
        # Verify the conversation was saved
        saved_conversation = current_app.conversations_col.find_one({
            "user_id": user_id,
            "created_at": {"$gte": start_of_day}
        })
        
        if saved_conversation:
            print(f"DEBUG: Successfully verified conversation save - messages: {len(saved_conversation.get('messages', []))}")
        else:
            print("DEBUG: ERROR - Could not verify conversation was saved")
            
        return True
    except Exception as e:
        print(f"ERROR saving conversation: {e}")
        return False

def safe_translate(text, source="auto", target="en", max_retries=2):
    """Safe translation with retries"""
    for attempt in range(max_retries):
        try:
            translated = GoogleTranslator(source=source, target=target).translate(text)
            return translated, source
        except Exception as e:
            print(f"Translation attempt {attempt + 1} failed: {e}")
            time.sleep(1)
    
    return text, "en"  # Fallback to English

def detect_and_translate(text, target_lang="en"):
    """Language detection and translation"""
    try:
        if target_lang == "en" and re.match(r'^[a-zA-Z0-9\s\.,!?@#$%^&*()_+-=]*$', text):
            return text, "en"
        
        translated, detected_lang = safe_translate(text, target=target_lang)
        print(f"DEBUG: Translated '{text}' to '{translated}' (detected: {detected_lang})")
        return translated, detected_lang
        
    except Exception as e:
        print(f"ERROR in language detection/translation: {e}")
        return text, "en"

def get_best_match(user_query, top_k=3):
    """Find the most similar Q&A pair using semantic search."""
    if model is None or qa_embeddings is None:
        return []
        
    try:
        query_embedding = model.encode(user_query, convert_to_tensor=True)
        scores = util.cos_sim(query_embedding, qa_embeddings)[0]
        top_results = torch.topk(scores, k=top_k)
        top_indices = top_results.indices.tolist()
        top_scores = top_results.values.tolist()
        
        # Return both indices and scores
        return list(zip(top_indices, top_scores))
    except Exception as e:
        print(f"ERROR in get_best_match: {e}")
        return []


@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_query = data.get("message", "").strip().lower()

    if not user_query:
        return jsonify({"reply": "Please type a message."})

    print(f"DEBUG: User query: {user_query}")

    # Step 1: Check if it's a greeting (only exact matches)
    user_query_lower = user_query.lower()
    for greet, response in GREETINGS.items():
        if user_query_lower == greet or user_query_lower.startswith(greet + ' '):
            if current_user.is_authenticated:
                save_conversation(str(current_user.id), user_query, response)
            return jsonify({"reply": response})

    # Step 2: Check for recommendation patterns
    recommendation_patterns = [
        'recommend', 'suggest', 'what should i watch', 'movies like', 'i want movies like',
        'similar to', 'good movies', 'best movies', 'what to watch','something similar to',
        'like', 'similar movies', 'suggestion', 'how about', 'what about','something like','give me some movie recommendations'
    ]
    
    if any(pattern in user_query_lower for pattern in recommendation_patterns):
        response = handle_recommendation_request(user_query)
        if current_user.is_authenticated:
            save_conversation(str(current_user.id), user_query, response)
        return jsonify({"reply": response})
        

    # Step 3: If models failed to load, use fallback
    if model is None or qa_embeddings is None or questions is None:
        response = random.choice(FALLBACK_RESPONSES)
        if current_user.is_authenticated:
            save_conversation(str(current_user.id), user_query, response)
        return jsonify({"reply": response})

    # Step 4: detect language + translate to English for processing
    translated_query, original_lang = detect_and_translate(user_query)
    print(f"DEBUG: Translated query: {translated_query}, Original lang: {original_lang}")

    # Step 5: semantic search with better matching
    results = get_best_match(translated_query, top_k=3)  # Get top 3 matches
    
    if not results:
        response = "I'm not sure about that. Try asking me about specific movies or recommendations!"
    else:
        # Find the best match with decent score
        best_match = None
        for idx, score in results:
            if score > 0.7:  # Higher threshold for better accuracy
                best_match = (idx, score)
                break
        
        
        if best_match:
            idx, score = best_match
            try:
                # Make sure the index is valid using the questions list
                if 0 <= idx < len(questions):
                    matched_question = questions[idx]
                    answer = answers[idx]
                    response = answer
                    print(f"DEBUG: Best match - Q: {matched_question}, Score: {score:.4f}")
                else:
                    print(f"DEBUG: Invalid index {idx}, questions length: {len(questions)}")
                    response = handle_unknown_query(user_query)
            except Exception as e:
                print(f"ERROR accessing QA data: {e}")
                # Fallback to simple response
                response = "I can help you with movie information! Try asking about specific movies."



    # Step 6: translate back if needed
    if original_lang != "en":
        try:
            response, _ = safe_translate(response, source="en", target=original_lang)
        except Exception as e:
            print(f"ERROR translating response back: {e}")

    # Save conversation if user is logged in
    if current_user.is_authenticated:
        save_conversation(str(current_user.id), user_query, response)

    return jsonify({"reply": response})

def handle_unknown_query(query):
    """Handle queries that don't match anything"""
    if 'popular' in query:
        return "I can check popularity for specific movies. Try asking 'Is [movie name] popular?'"
    elif 'rating' in query:
        return "I can check ratings for specific movies. Try asking 'What's the rating of [movie name]?'"
    elif 'about' in query:
        return "I can tell you about specific movies. Try asking 'Tell me about [movie name]'"
    else:
        return "I'm not sure I understand. Try asking about specific movies, ratings, popularity, or recommendations!"

@chatbot_bp.route("/conversations")
def get_conversations():
    """API endpoint - returns JSON conversation list"""
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        conversations = current_app.conversations_col.find(
            {"user_id": str(current_user.id)}
        ).sort("updated_at", -1)
        
        conversation_list = []
        for conv in conversations:
            conversation_list.append({
                "id": str(conv["_id"]),
                "date": conv["created_at"].strftime("%Y-%m-%d"),
                "message_count": len(conv.get("messages", [])),
                "last_message": conv.get("messages", [])[-1]["user"] if conv.get("messages") else ""
            })
        
        return jsonify({"conversations": conversation_list})  # JSON response
    except Exception as e:
        print(f"ERROR getting conversations: {e}")
        return jsonify({"error": "Failed to get conversations"}), 500  # JSON response

@chatbot_bp.route("/conversation/<conversation_id>")
def get_conversation(conversation_id):
    """API endpoint - returns JSON conversation details"""
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        conversation = current_app.conversations_col.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": str(current_user.id)
        })
        
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404  # JSON response
        
        return jsonify({  # JSON response
            "id": str(conversation["_id"]),
            "date": conversation["created_at"].strftime("%Y-%m-%d %H:%M"),
            "messages": conversation.get("messages", [])
        })
    except Exception as e:
        print(f"ERROR getting conversation: {e}")
        return jsonify({"error": "Failed to get conversation"}), 500 
    
@chatbot_bp.route("/clear_messages/<conversation_id>", methods=["POST"])
def clear_messages(conversation_id):
    """Clear messages from a specific conversation"""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    try:
        # Clear messages but keep the conversation
        result = current_app.conversations_col.update_one(
            {
                "_id": ObjectId(conversation_id),
                "user_id": str(current_user.id)
            },
            {
                "$set": {
                    "messages": [], 
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"DEBUG: Cleared messages from conversation {conversation_id}")
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Conversation not found"}), 404
            
    except Exception as e:
        print(f"ERROR clearing messages: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@chatbot_bp.route("/clear_chats", methods=["POST"])
def clear_all_chats():
    """Clear all chat conversations for the current user"""
    print("DEBUG: clear_all_chats route called")  # Debug log
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    try:
        # Delete all conversations for the current user
        result = current_app.conversations_col.delete_many({
            "user_id": str(current_user.id)
        })
        
        print(f"DEBUG: Cleared {result.deleted_count} conversations for user {current_user.id}")
        return jsonify({"success": True, "deleted_count": result.deleted_count})
        
    except Exception as e:
        print(f"ERROR clearing chats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@chatbot_bp.route("/delete_conversation/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    """Delete a specific conversation"""
    print(f"DEBUG: delete_conversation route called for {conversation_id}")  # Debug log
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    try:
        # Delete the specific conversation
        result = current_app.conversations_col.delete_one({
            "_id": ObjectId(conversation_id),
            "user_id": str(current_user.id)
        })
        
        print(f"DEBUG: Delete result - matched: {result.matched_count}, deleted: {result.deleted_count}")
        
        if result.deleted_count > 0:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Conversation not found"}), 404
            
    except Exception as e:
        print(f"ERROR deleting conversation: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@chatbot_bp.route("/test_delete", methods=["DELETE"])
def test_delete():
    """Test if DELETE routes are working"""
    return jsonify({"success": True, "message": "DELETE route works!"})
