# generate_movie_qa_dataset.py
import pandas as pd
import numpy as np

def generate_qa_dataset():
    # Load the original movie data
    movies_df = pd.read_excel('data/movies_with_features.xlsx')
    
    # Initialize list to store Q&A pairs
    qa_data = []
    
    for _, row in movies_df.iterrows():
        title = row['title']
        overview = row.get('overview', 'No overview available.')
        vote_average = row.get('vote_average', 0)
        vote_count = row.get('vote_count', 0)
        popularity = row.get('popularity', 0)
        
        # Clean the overview text
        overview_clean = overview.replace('\n', ' ').strip() if pd.notna(overview) else 'No overview available.'
        
        # Generate multiple Q&A pairs for each movie
        qa_pairs = [
            {
                'question': f"What is the movie '{title}' about?",
                'answer': f"📖 Here's the plot of *{title}*: {overview_clean}",
                'movie_title': title,
                'vote_average': vote_average,
                'vote_count': vote_count,
                'popularity': popularity
            },
            {
                'question': f"Tell me about '{title}'",
                'answer': f"🎥 *{title}* is about: {overview_clean}.",
                'movie_title': title,
                'vote_average': vote_average,
                'vote_count': vote_count,
                'popularity': popularity
            },
            {
                'question': f"Is {title} a good movie?",
                'answer': f"⭐ Well *{title}* has a rating of {vote_average}/10 based on {vote_count} votes.",
                'movie_title': title,
                'vote_average': vote_average,
                'vote_count': vote_count,
                'popularity': popularity
            },
            {
                'question': f"How popular is {title}?",
                'answer': f" Let me check ! 📊 *{title}* has a popularity score of {popularity:.2f}.",
                'movie_title': title,
                'vote_average': vote_average,
                'vote_count': vote_count,
                'popularity': popularity
            },
            {
                'question': f"Should I watch {title}?",
                'answer': f"🎯As i see *{title}* has a {vote_average}/10 rating so what do you think 🎬🍿? ",
                'movie_title': title,
                'vote_average': vote_average,
                'vote_count': vote_count,
                'popularity': popularity
            }
        ]
        
        qa_data.extend(qa_pairs)
    
    # Create DataFrame
    qa_df = pd.DataFrame(qa_data)
    
    # Save to Excel
    qa_df.to_excel('data/movie_qa_dataset.xlsx', index=False)
    
    print(f"✅ Generated {len(qa_df)} Q&A pairs for {len(movies_df)} movies")
    print(f"💾 Saved to data/movie_qa_dataset.xlsx")
    print(f"📊 Columns: {', '.join(qa_df.columns.tolist())}")
    
    # Show sample
    print("\n📋 Sample Q&A pairs:")
    print(qa_df[['question', 'answer']].head(3))
    
    return qa_df

if __name__ == "__main__":
    generate_qa_dataset()