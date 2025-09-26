# generate_qa_embeddings.py
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
import pickle
from pathlib import Path
import os

def create_chatbot_model():
    """Generate Q&A embeddings for movie chatbot"""
    Path('chatbot_model').mkdir(exist_ok=True)
    
    # Load Q&A dataset
    print("📖 Loading Q&A dataset...")
    df = pd.read_excel('data/movie_qa_dataset.xlsx')
    questions = df['question'].tolist()
    answers = df['answer'].tolist()
    
    print(f"✅ Loaded {len(questions)} Q&A pairs")
    
    # Set offline mode to prevent internet requests
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['HF_DATASETS_OFFLINE'] = '1'
    
    # Load model (will use cache if available)
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
        print("✅ Model loaded from local cache")
    except Exception as e:
        print(f"❌ Cache load failed: {e}")
        print("🔧 Attempting to download model...")
        # Fallback to online download
        os.environ['TRANSFORMERS_OFFLINE'] = '0'  # Enable online
        model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Generate embeddings
    print("⚡ Generating embeddings...")
    question_embeddings = model.encode(questions, convert_to_tensor=True, show_progress_bar=True)
    
    # Save dataset
    output_data = {
        'questions': questions,
        'answers': answers,
        'embeddings': question_embeddings.cpu(),
        'dataframe': df,
        'model_name': 'all-MiniLM-L6-v2'
    }
    
    with open('chatbot_model/qa_dataset.pkl', 'wb') as f:
        pickle.dump(output_data, f)
    
    print(f"✅ Saved embeddings for {len(questions)} questions to chatbot_model/qa_dataset.pkl")
    return output_data

if __name__ == "__main__":
    create_chatbot_model()