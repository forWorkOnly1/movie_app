from flask import Flask
from app.extensions import Bcrypt, LoginManager
from flask_mail import Mail
from pymongo import MongoClient
from config import Config
from datetime import datetime

# Create extension instances
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
login_manager.login_view = 'auth.login'

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        return timestamp
    try:
        return timestamp.strftime("%Y-%m-%d %H:%M")
    except:
        return str(timestamp)


def create_app(config_class=Config):
    # Remove the "../" since templates and static are now inside app/
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    # Initialize extensions
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    try:
        client = MongoClient(app.config['MONGO_URI'])
        app.db = client["movie_app"]
        
        # Create collections if they don't exist
        collections_to_create = ['users', 'chats', 'conversations']
        existing_collections = app.db.list_collection_names()
        
        for collection in collections_to_create:
            if collection not in existing_collections:
                app.db.create_collection(collection)
                print(f"DEBUG: Created collection: {collection}")
        
        # Assign collections
        app.users_col = app.db["users"]
        app.chats_col = app.db["chats"]  
        app.conversations_col = app.db["conversations"]  
        
        print("DEBUG: MongoDB connected successfully")
        print(f"DEBUG: Existing collections: {existing_collections}")
        print(f"DEBUG: Using collections: users, chats, conversations")
        
    except Exception as e:
        print(f"ERROR: MongoDB connection failed: {e}")
    
    # Register template filters
    from app.utils import runtime_to_hm
    app.jinja_env.filters['runtime_to_hm'] = runtime_to_hm
    app.jinja_env.filters['format_timestamp'] = format_timestamp

    # Register blueprints
    from app.routes import main_bp
    from app.auth import auth_bp
    from app.chatbot import chatbot_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chatbot_bp)
    
    return app