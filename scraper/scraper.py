from bs4 import BeautifulSoup
import json
import os
import requests

URLS = {
    "Are You The One": "https://scnlog.me/?s=are%20you%20the%20one%20reality",
    "Love Island VIP": "https://scnlog.me/?s=Love%20island%20vip%20german",
    "CoupleChallenge": "https://scnlog.me/?s=Couplechallenge",
    "Temptation Island VIP": (
        "https://scnlog.me/?s=Temptation%20island%20vip%20german"
    ),
    "Sommerhaus": "https://scnlog.me/?s=Sommerhaus",
}

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )
}

all_data = {}

for category, url in URLS.items():
  try:
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")
      items = []

      # Passe den Selektor an die Struktur von scnlog.me an (meistens h2 a oder h3 a für Beiträge)
      for post in soup.select("h2.title a, h3.entry-title a, h2 a")[:5]:
        title = post.get_text(strip=True)
        link = post.get("href")
        if title and link:
          items.append({"title": title, "link": link})

      all_data[category] = items
    else:
      all_data[category] = []
  except Exception as e:
    print(f"Fehler bei {category}: {e}")
    all_data[category] = []

# Speichern als JSON für das Frontend
os.makedirs(".", exist_ok=True)
with open("data.json", "w", encoding="utf-8") as f:
  json.dump(all_data, f, ensure_ascii=False, indent=4)

print("Scraping beendet und data.json aktualisiert.")
