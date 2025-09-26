import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://www.imdb.com/chart/top/"
headers = {"Accept-Language": "en-US,en;q=0.5"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

movies = []
for row in soup.select('tbody.lister-list tr'):
    title = row.find('td', class_='titleColumn').a.text
    year = row.find('span', class_='secondaryInfo').text.strip("()")
    rating = row.find('td', class_='ratingColumn imdbRating').strong.text
    link = "https://www.imdb.com" + row.find('a')['href']
    movies.append({"title": title, "year": year, "rating": rating, "link": link})

df = pd.DataFrame(movies)
df.to_csv("top_imdb_movies.csv", index=False)
print(df.head())
