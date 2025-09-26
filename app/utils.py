import re
import requests
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from rapidfuzz import process
from flask import request, current_app
from functools import lru_cache
from flask_mail import Message
import os
from app import mail

def send_email(recipient, subject, body, html=False):
    try:
        from flask_mail import Message
        from flask import current_app
        
        print(f"DEBUG: Attempting to send email to {recipient}")
        
        # Get mail instance from current app extensions
        mail = current_app.extensions.get('mail')
        if mail is None:
            print("ERROR: Mail extension not found")
            return False
            
        # Check if email credentials are configured
        if not current_app.config.get('MAIL_USERNAME') or not current_app.config.get('MAIL_PASSWORD'):
            print("ERROR: Email credentials not configured")
            return False
            
        # Use the email from config or default
        sender_email = current_app.config.get('MAIL_USERNAME', 'noreply@movieapp.com')
        sender_name = current_app.config.get('MAIL_DEFAULT_SENDER_NAME', 'Movie App')
        
        print(f"DEBUG: Sending from {sender_email} to {recipient}")
        
        # Create message
        msg = Message(
            subject=subject,
            recipients=[recipient],
            sender=(sender_name, sender_email),
            reply_to=current_app.config.get('MAIL_REPLY_TO', 'support@movieapp.com')
        )
        
        # Add headers to improve deliverability and avoid spam
        msg.extra_headers = {
            'X-Mailer': 'Movie App',
            'X-Priority': '3',
            'X-MSMail-Priority': 'Normal',
            'List-Unsubscribe': '<mailto:support@movieapp.com?subject=Unsubscribe>',
            'Precedence': 'bulk',
            'X-Auto-Response-Suppress': 'OOF',
        }
        
        # Add important headers to avoid being marked as spam
        msg.extra_headers['MIME-Version'] = '1.0'
        msg.extra_headers['Content-Type'] = 'text/html; charset="utf-8"' if html else 'text/plain; charset="utf-8"'
        
        if html:
            msg.html = body
        else:
            msg.body = body
            
        # Send the message
        mail.send(msg)
        print(f"DEBUG: Email sent successfully to {recipient}")
        return True
        
    except Exception as e:
        print(f"ERROR sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Initialize dataset (will be loaded once)
df = None
tfidf_matrix = None

def load_dataset(data_path):
    global df, tfidf_matrix
    try:
        if data_path is None:
            data_path = 'data/movies_with_features.xlsx' 
            
        print(f"DEBUG: Trying to load dataset from: {data_path}")
        
        # Check if file exists
        if not os.path.exists(data_path):
            print(f"ERROR: Dataset file not found at: {data_path}")
            df = None
            tfidf_matrix = None
            return False
            
        # Load the dataset
        if data_path.endswith('.xlsx'):
            df = pd.read_excel(data_path)
        elif data_path.endswith('.csv'):
            df = pd.read_csv(data_path)
        else:
            print(f"ERROR: Unsupported file format: {data_path}")
            df = None
            tfidf_matrix = None
            return False
            
        print(f"DEBUG: Dataset loaded with {len(df)} rows")
        print(f"DEBUG: Dataset columns: {df.columns.tolist()}")
        
        # Check if required columns exist
        if 'title' not in df.columns:
            print("ERROR: Dataset missing 'title' column")
            df = None
            tfidf_matrix = None
            return False
            
        if 'combined_features' not in df.columns:
            print("WARNING: Dataset missing 'combined_features' column, creating dummy column")
            df['combined_features'] = df['title']  # Use title as fallback
            
        df["title"] = df["title"].astype(str)
        df["title_clean"] = df["title"].str.strip().str.lower()
        
        # Create TF-IDF matrix
        tfidf = TfidfVectorizer(stop_words="english")
        combined = df["combined_features"].fillna("")
        tfidf_matrix = tfidf.fit_transform(combined)
        
        print("DEBUG: TF-IDF matrix created successfully")
        return True
        
    except Exception as e:
        print(f"ERROR loading dataset: {e}")
        df = None
        tfidf_matrix = None
        return False

# Content filtering
BLOCKED_PATTERN = re.compile(r"\b(sex|porn|xxx|erotic)\b", re.IGNORECASE)

def is_blocked_movie(title: str, overview: str) -> bool:
    text = f"{title or ''} {overview or ''}"
    return bool(BLOCKED_PATTERN.search(text))

# Password validation - Updated to match HTML pattern
PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$"
)

def validate_password(password: str) -> bool:
    return bool(PASSWORD_REGEX.match(password))

# HTTP utilities
def safe_get(url, params=None, timeout=8):
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

def get_user_country_guess():
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        data = safe_get(f"https://ipapi.co/{ip}/json/")
        return data.get("country_code", "US")
    except Exception:
        return "US"

# Template filter
def runtime_to_hm(runtime_minutes):
    try:
        m = int(runtime_minutes or 0)
        h, mm = divmod(m, 60)
        if h > 0:
            return f"{h}h {mm}m"
        return f"{mm}m"
    except Exception:
        return "—"

# Recommendation utilities
def find_multiple_close_titles(query: str, limit=3, threshold=80):
    if df is None:
        print("DEBUG: Dataset is None in find_multiple_close_titles")
        return []
        
    matches = process.extract(query.lower(), df["title_clean"].tolist(), limit=limit)
    picks = []
    for match_title, score, idx in matches:
        if score >= threshold:
            picks.append(df.iloc[idx]["title"])  
    return picks

# Add a function to check dataset status
def check_dataset_status():
    """Check if dataset is loaded properly"""
    if df is None:
        print("DEBUG: df is None")
        return False
    if tfidf_matrix is None:
        print("DEBUG: tfidf_matrix is None")
        return False
    print("DEBUG: Dataset and TF-IDF matrix are loaded")
    return True