# Movie App 🎬

A modern web application for movie enthusiasts built with Python and Flask. Discover, search, and get recommendations for your favorite movies with AI-powered chatbot assistance.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-red.svg)
![TMDB](https://img.shields.io/badge/Data-TMDB_API-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- **🎥 Movie Search** - Find movies by title, genre, or actor using TMDB API
- **🤖 AI Chatbot** - Get personalized movie recommendations using semantic search
- **💬 Chat History** - Save and manage your conversations with delete functionality
- **🎯 Smart Recommendations** - AI-powered movie suggestions combining dataset + TMDB
- **📊 Hybrid Database** - Local dataset + real-time TMDB data
- **🌍 Multi-language Support** - Chatbot understands and responds in multiple languages
- **📱 Responsive Design** - Works perfectly on desktop and mobile devices

## ⚠️ Prerequisites

### TMDB API Key Required
This app uses **The Movie Database (TMDB) API** for:
- Real-time movie searches
- Fresh movie recommendations  
- Up-to-date ratings and metadata
- Movie posters and images

**Get your free API key:**
1. Go to [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)
2. Create a free account
3. Request an API key
4. Add it to your `.env` file

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/forWorkOnly1/movie_app.git
cd movie-app
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file:
```bash
# Windows
copy .env.example .env
```

Edit `.env` with your TMDB API key:
```env
TMDB_API_KEY=your_actual_tmdb_api_key_here
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
```

### 5. Run the Application
```bash
python app.py
```

### 6. Open your browser to `http://localhost:5000`

## 🔄 Data Generation (Optional)

The app comes with pre-generated data, but you can regenerate it:

```bash
# Generate Q&A dataset from movie data
python scripts/generate_movie_qa_dataset.py

# Generate AI embeddings for the chatbot
python scripts/generate_qa_embeddings.py
```

## 📁 Project Structure

```
movie_app/
├── app/                 # Flask application
│   ├── static/         # CSS, JS, images
│   ├── templates/      # HTML templates
│   ├── chatbot.py      # AI chatbot with TMDB integration
│   ├── tmdb.py         # TMDB API functions
│   └── ...             # Other app files
├── data/               # Movie datasets
│   ├── movies_with_features.xlsx    # Original movie data
│   └── movie_qa_dataset.xlsx        # Generated Q&A pairs
├── scripts/            # Data generation scripts
│   ├── generate_movie_qa_dataset.py # Creates Q&A from movie data
│   └── generate_qa_embeddings.py    # Generates AI embeddings
├── chatbot_model/      # AI model files
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## 🎯 How It Works

### Hybrid Recommendation System:
1. **Local Dataset**: 147,315 pre-generated Q&A pairs for instant responses
2. **TMDB API**: Real-time movie data for fresh recommendations
3. **AI Semantic Search**: Finds the most relevant answers using sentence transformers

### Example Queries & Sources:
- "What is Inception about?" → **Local dataset** (fast response)
- "Recommend movies like The Matrix" → **TMDB API** (fresh recommendations)
- "Is the new Batman movie good?" → **TMDB API** (current data)
- "Tell me about classic movies" → **Local dataset** (comprehensive)

## 🤖 AI Chatbot Features

The chatbot intelligently combines both data sources:

- **📖 Plot Summaries**: From local dataset (fast)
- **🎯 Recommendations**: From TMDB (up-to-date)
- **⭐ Ratings & Reviews**: From TMDB (current)
- **🎬 New Releases**: From TMDB (fresh data)
- **📚 Classic Movies**: From local dataset (comprehensive)

## 💾 Included Data Files

### For Immediate Use:
- `data/movie_qa_dataset.xlsx` - 147,315 Q&A pairs (ready to use)
- `data/movies_with_features.xlsx` - Base movie dataset

### Regeneratable:
- `chatbot_model/qa_dataset.pkl` - Can be regenerated from Excel files
- `chatbot_model/qa_embeddings.pt` - AI embeddings (regeneratable)

## 🔧 Development

### Environment Setup
```bash
# Create .env file from template
cp .env.example .env

# Edit .env and add your TMDB API key
nano .env  # or use any text editor
```

### Regenerating Data
```bash
# Generate Q&A pairs (requires movies_with_features.xlsx)
python scripts/generate_movie_qa_dataset.py

# Generate AI embeddings (requires movie_qa_dataset.xlsx)  
python scripts/generate_qa_embeddings.py
```

## 📦 Dependencies

Key packages include:
- `flask` - Web framework
- `sentence-transformers` - AI semantic search
- `requests` - TMDB API calls
- `pandas` - Excel file processing
- `python-dotenv` - Environment variables

## 🎯 Usage Examples

```bash
# With TMDB API key - Full functionality
TMDB_API_KEY=your_key_here python app.py

# Without TMDB API key - Limited functionality (dataset only)
python app.py
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines.

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **The Movie Database (TMDB)** for providing the excellent API
- HuggingFace for sentence transformer models
- Flask community for web framework

---


**⭐ Remember to get your free TMDB API key for full functionality!**