from flask_login import UserMixin
from bson.objectid import ObjectId
from app import login_manager
from flask import current_app
from datetime import datetime

class User(UserMixin):
    def __init__(self, doc):
        self.id = str(doc["_id"])
        self.username = doc["username"]
        self.email = doc.get("email")
        self.verified = doc.get("verified", False)

@login_manager.user_loader
def load_user(user_id):
    try:
        doc = current_app.users_col.find_one({"_id": ObjectId(user_id)})
        return User(doc) if doc else None
    except Exception:
        return None