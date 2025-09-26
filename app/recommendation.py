from app.tmdb import search_movie, make_card_from_tmdb_obj, tmdb_similar
from app.utils import linear_kernel  # Only import what we need

def recommend_from_dataset(title: str, top_n=8, country="US"):
    # Import df and tfidf_matrix dynamically to avoid timing issues
    from app.utils import df, tfidf_matrix
    
    if df is None or tfidf_matrix is None:
        print("DEBUG: Dataset or TF-IDF matrix not loaded in recommend_from_dataset")
        return []
        
    key = title.strip().lower()
    print(f"DEBUG: Looking for '{key}' in dataset")
    
    if key not in set(df["title_clean"].values):
        print(f"DEBUG: '{key}' not found in dataset")
        return []

    idx = df.index[df["title_clean"] == key][0]
    sims = linear_kernel(tfidf_matrix[idx:idx+1], tfidf_matrix).flatten()
    order = sims.argsort()[::-1]
    order = [i for i in order if i != idx][:top_n]

    cards = []
    for i in order:
        title_i = df.iloc[i]["title"]
        print(f"DEBUG: Similar movie found: {title_i}")
        tm = search_movie(title_i)
        if tm:
            print(f"DEBUG: TMDB found: {tm.get('title')}")
            card = make_card_from_tmdb_obj(tm, country)
            if card:
                cards.append(card)
                print(f"DEBUG: Added card for: {card.get('title')}")
        else:
            print(f"DEBUG: TMDB not found for: {title_i}")
    
    print(f"DEBUG: Total cards from dataset: {len(cards)}")
    return cards

def recommend_fallback_tmdb(title: str, top_n=8, country="US"):
    print(f"DEBUG: Trying TMDB fallback for: {title}")
    found = search_movie(title)
    if not found:
        print("DEBUG: TMDB search returned no results")
        return []
    
    print(f"DEBUG: TMDB found: {found.get('title')}")
    similar = tmdb_similar(found.get("id"), limit=top_n)
    print(f"DEBUG: TMDB similar movies: {len(similar)} found")
    
    cards = [make_card_from_tmdb_obj(m, country) for m in similar]
    valid_cards = [c for c in cards if c]
    print(f"DEBUG: Valid TMDB cards: {len(valid_cards)}")
    
    return valid_cards