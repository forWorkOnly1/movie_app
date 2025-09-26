from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.utils import get_user_country_guess, find_multiple_close_titles, load_dataset
from app.tmdb import tmdb_trending, make_card_from_tmdb_obj
from app.recommendation import recommend_from_dataset, recommend_fallback_tmdb
import asyncio
from bson import ObjectId

main_bp = Blueprint('main', __name__)

@main_bp.record_once
def on_load(state):
    print("DEBUG: Loading dataset...")
    data_path = state.app.config.get('DATA_PATH', 'data/movies_with_features.xlsx')  # Updated path
    load_dataset(data_path)
    print("DEBUG: Dataset loaded")
    
@main_bp.route("/", methods=["GET", "POST"])
def index():
    auto_country = get_user_country_guess()
    country = request.form.get("country", auto_country)

    query = ""
    not_found_message = None
    recommendations = []

    trending_cards = [make_card_from_tmdb_obj(m, country) for m in tmdb_trending(limit=8)]
    trending = [c for c in trending_cards if c]

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Please log in to search and get recommendations.", "warning")
            return redirect(url_for("auth.login"))

        query = request.form.get("movie_name", "").strip()
        print(f"DEBUG: Search query: '{query}'")
        
        if query:
            # Import dynamically to avoid timing issues
            from app.utils import find_multiple_close_titles
            from app.recommendation import recommend_from_dataset, recommend_fallback_tmdb
            
            matched_titles = find_multiple_close_titles(query, limit=3, threshold=82)
            print(f"DEBUG: Matched titles: {matched_titles}")
            
            if matched_titles:
                pool = []
                for t in matched_titles:
                    print(f"DEBUG: Getting recommendations for: {t}")
                    recs = recommend_from_dataset(t, top_n=4, country=country)
                    print(f"DEBUG: Recommendations for {t}: {len(recs)} found")
                    pool.extend(recs)
                
                seen, out = set(), []
                for c in pool:
                    key = c.get("id") or c.get("title")
                    if key not in seen:
                        seen.add(key)
                        out.append(c)
                recommendations = out
                print(f"DEBUG: Total unique recommendations: {len(recommendations)}")
            else:
                print("DEBUG: No close matches found, trying TMDB fallback")
                recommendations = recommend_fallback_tmdb(query, top_n=8, country=country)
                print(f"DEBUG: TMDB fallback recommendations: {len(recommendations)} found")
                if not recommendations:
                    not_found_message = "Sorry — couldn't find that movie in our dataset or on TMDB."

    return render_template(
        "index.html",
        query=query,
        country=country,
        recommendations=recommendations,
        trending=trending,
        not_found_message=not_found_message,
        user=current_user
    )
@main_bp.route("/suggest")
def suggest():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify({"suggestions": []})
    
    # Import dynamically
    from app.utils import df
    
    if df is None:
        print("DEBUG: Dataset not loaded for suggestions")
        return jsonify({"suggestions": []})
        
    titles = [t for t in df["title"].tolist() if q in t.lower()]
    print(f"DEBUG: Suggestions for '{q}': {titles[:5]}")
    return jsonify({"suggestions": titles[:5]})


@main_bp.route("/debug-chats")
@login_required
def debug_chats():
    """Debug route to check what's in the collections"""
    try:
        from flask import current_app
        import json
        
        debug_info = {
            "user_id": str(current_user.id),
            "collections_exist": {
                "users": current_app.users_col is not None,
                "chats": current_app.chats_col is not None,
                "conversations": current_app.conversations_col is not None
            },
            "conversations_count": current_app.conversations_col.count_documents({"user_id": str(current_user.id)}),
            "chats_count": current_app.chats_col.count_documents({"user_id": str(current_user.id)}),
            "conversations": list(current_app.conversations_col.find({"user_id": str(current_user.id)}).sort("created_at", -1).limit(5)),
            "chats": list(current_app.chats_col.find({"user_id": str(current_user.id)}).sort("created_at", -1).limit(5))
        }
        
        # Convert ObjectId to string for JSON serialization
        for conv in debug_info["conversations"]:
            conv["_id"] = str(conv["_id"])
        for chat in debug_info["chats"]:
            chat["_id"] = str(chat["_id"])
            
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({"error": str(e)})
    
@main_bp.route("/chat-history")
@login_required
def chat_history():
    """HTML page - displays chat history"""
    try:
        # Fetch user's chats from database
        conversations = current_app.conversations_col.find(
            {"user_id": str(current_user.id)}
        ).sort("updated_at", -1)
        
        # Convert to list for the template
        chat_list = []
        for conv in conversations:
            messages = conv.get("messages", [])
            last_message = "No messages"
            
            if messages:
                # Get the last message (whether from user or bot)
                last_msg = messages[-1]
                if 'user' in last_msg and last_msg['user']:
                    last_message = f"You: {last_msg['user'][:50]}..."
                elif 'bot' in last_msg and last_msg['bot']:
                    last_message = f"Bot: {last_msg['bot'][:50]}..."
            
            chat_list.append({
                "id": str(conv["_id"]),
                "date": conv["created_at"].strftime("%Y-%m-%d"),
                "message_count": len(messages),
                "last_message": last_message
            })
        
        return render_template("conversations.html", chats=chat_list)
    except Exception as e:
        print(f"ERROR fetching chats: {e}")
        return render_template("conversations.html", chats=[])

@main_bp.route("/conversation/<conversation_id>")
@login_required
def view_conversation(conversation_id):
    """HTML page - displays specific conversation"""
    try:
        conversation = current_app.conversations_col.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": str(current_user.id)
        })
        
        if not conversation:
            flash("Conversation not found", "error")
            return redirect(url_for('main.chat_history'))
        
        # Format the conversation data for template
        formatted_conversation = {
            "id": str(conversation["_id"]),
            "date": conversation["created_at"].strftime("%Y-%m-%d %H:%M"),
            "messages": conversation.get("messages", [])
        }
        
        return render_template("conversation_detail.html", 
                             conversation=formatted_conversation)  # HTML response
        
    except Exception as e:
        print(f"ERROR viewing conversation: {e}")
        flash("Error loading conversation", "error")
        return redirect(url_for('main.chat_history'))