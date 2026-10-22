from bs4 import BeautifulSoup
import cloudscraper
import json
import os

URLS = {
    "Are You The One": "https://scnlog.me/?s=are%20you%20the%20one%20reality",
    "Love Island VIP": "https://scnlog.me/?s=Love%20island%20vip%20german",
    "CoupleChallenge": "https://scnlog.me/?s=Couplechallenge",
    "Temptation Island VIP": (
        "https://scnlog.me/?s=Temptation%20island%20vip%20german"
    ),
    "Sommerhaus": "https://scnlog.me/?s=Sommerhaus",
}

# Cloudscraper umgeht gängige Bot-Schutzmauern (wie Cloudflare)
scraper = cloudscraper.create_scraper()

all_data = {}

for category, url in URLS.items():
  try:
    response = scraper.get(url, timeout=15)
    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")
      items = []

      # Universellerer Selektor, der meistens greift (sucht alle Links innerhalb von Beiträgen)
      # Wir durchsuchen gängige WordPress-Klassen oder Artikel-Links
      for post in soup.select("h2 a, h3 a, .entry-title a")[:15]:
        title = post.get_text(strip=True)
        link = post.get("href")

        # Filtern von unnötigen Links (z.B. Kategorien oder Seiten-Navigation)
        if title and link and "scnlog.me" in link and "?" not in title:
          # Duplikate vermeiden
          if not any(item["link"] == link for item in items):
            items.append({"title": title, "link": link})

        if len(items) >= 5:
          break

      all_data[category] = items
    else:
      print(f"Fehler bei {category}: HTTP Status {response.status_code}")
      all_data[category] = []
  except Exception as e:
    print(f"Fehler bei {category}: {e}")
    all_data[category] = []

# Speichern als JSON
os.makedirs(".", exist_ok=True)
with open("data.json", "w", encoding="utf-8") as f:
  json.dump(all_data, f, ensure_ascii=False, indent=4)

print("Scraping beendet und data.json aktualisiert.")
