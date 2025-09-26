import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'you-will-never-guess')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    TMDB_API_KEY = os.getenv('TMDB_API_KEY')
    DATA_PATH = os.getenv('DATA_PATH', 'data/movies_with_features.xlsx') 
    
    # Email configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Chatbot Model Paths (Updated paths)
    #CHATBOT_MODEL_PATH = os.getenv('CHATBOT_MODEL_PATH', 'chatbot_model/chatbot_model')

    CHATBOT_MODEL_PATH = os.getenv('CHATBOT_MODEL_PATH', 'chatbot_model')
    QA_DATASET_PATH = os.getenv('QA_DATASET_PATH', 'chatbot_model/qa_dataset.pkl')
    QA_EMBEDDINGS_PATH = os.getenv('QA_EMBEDDINGS_PATH', 'chatbot_model/qa_embeddings.pt')