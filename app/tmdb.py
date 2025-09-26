from flask import current_app
from app.utils import safe_get, is_blocked_movie
import requests

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

def tmdb_request(endpoint: str, api_key: str, params=None):
    """Helper to call TMDB API safely."""
    url = f"https://api.themoviedb.org/3/{endpoint}"
    if params is None:
        params = {}
    params["api_key"] = api_key
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[TMDB ERROR] {e}")
        return {}

def search_movie(title, api_key=None, language="en-US"):
    if api_key is None:
        api_key = current_app.config["TMDB_API_KEY"]
    data = tmdb_request("search/movie", api_key, {"query": title, "language": language})
    if data and data.get("results"):
        first = data["results"][0]
        return {
            "id": first["id"],
            "title": first.get("title"),
            "overview": first.get("overview"),
            "rating": first.get("vote_average"),
            "release_date": first.get("release_date")
        }
    return None

def tmdb_movie_details(movie_id: int):
    api_key = current_app.config["TMDB_API_KEY"]
    return tmdb_request(f"movie/{movie_id}", api_key)

# -----------------------------
# Recommendations & Similar
# -----------------------------
def tmdb_similar(movie_id: int, limit=8):
    api_key = current_app.config["TMDB_API_KEY"]
    data = tmdb_request(f"movie/{movie_id}/similar", api_key, {"page": 1})
    results = data.get("results", []) if data else []
    return results[:limit]

def tmdb_recommendations(movie_id: int, limit=8):
    api_key = current_app.config["TMDB_API_KEY"]
    data = tmdb_request(f"movie/{movie_id}/recommendations", api_key, {"page": 1})
    results = data.get("results", []) if data else []
    return results[:limit]

# Alias for chatbot.py compatibility
get_recommendations = tmdb_recommendations

# -----------------------------
# Trending & Genres
# -----------------------------
def tmdb_trending(limit=8):
    api_key = current_app.config["TMDB_API_KEY"]
    data = tmdb_request("trending/movie/week", api_key)
    results = data.get("results", []) if data else []
    return results[:limit]

_genre_cache = {"list": [], "map": {}}

def tmdb_genres():
    """Fetch and cache genres."""
    api_key = current_app.config["TMDB_API_KEY"]
    global _genre_cache
    if _genre_cache["list"]:
        return _genre_cache
    data = tmdb_request("genre/movie/list", api_key)
    genres = data.get("genres", []) if data else []
    name_to_id = {g["name"].lower(): g["id"] for g in genres}
    _genre_cache = {"list": genres, "map": name_to_id}
    return _genre_cache

def tmdb_discover_by_genre(genre_name: str, limit=8):
    api_key = current_app.config["TMDB_API_KEY"]
    g = tmdb_genres()
    gid = g["map"].get(genre_name.lower())
    if not gid:
        return []
    data = tmdb_request(
        "discover/movie",
        api_key,
        {"with_genres": gid, "sort_by": "popularity.desc", "page": 1},
    )
    results = data.get("results", []) if data else []
    return results[:limit]

# -----------------------------
# Watch link
# -----------------------------
def tmdb_watch_link(movie_id: int, country: str = "US"):
    api_key = current_app.config["TMDB_API_KEY"]
    data = tmdb_request(f"movie/{movie_id}/watch/providers", api_key)
    if not data:
        return None
    return data.get("results", {}).get(country, {}).get("link")

# -----------------------------
# Movie card for front-end
# -----------------------------
def make_card_from_tmdb_obj(tmdb_movie_obj: dict, country: str = "US"):
    if not tmdb_movie_obj or tmdb_movie_obj.get("adult"):
        return None

    movie_id = tmdb_movie_obj.get("id")
    details = tmdb_movie_details(movie_id)
    if not details:
        return None

    title = details.get("title")
    overview = details.get("overview") or ""
    if is_blocked_movie(title, overview):
        return None

    poster_path = details.get("poster_path")
    poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None
    genres = [g.get("name") for g in details.get("genres", []) if g.get("name")]

    return {
        "id": movie_id,
        "title": title,
        "poster": poster_url,
        "overview": overview,
        "rating": details.get("vote_average"),
        "release_date": details.get("release_date"),
        "runtime": details.get("runtime"),
        "genres": genres,
        "watch_link": tmdb_watch_link(movie_id, country),
        "tmdb_url": f"https://www.themoviedb.org/movie/{movie_id}",
    }

# -----------------------------
# Movie credits
# -----------------------------
def tmdb_movie_credits(movie_id: int):
    api_key = current_app.config["TMDB_API_KEY"]
    return tmdb_request(f"movie/{movie_id}/credits", api_key)