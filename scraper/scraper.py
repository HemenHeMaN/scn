import json
import os

import cloudscraper
from bs4 import BeautifulSoup

URLS = {
    "Are You The One": "https://scnlog.me/?s=are%20you%20the%20one%20reality",
    "Love Island VIP": "https://scnlog.me/?s=Love%20island%20vip%20german",
    "CoupleChallenge": "https://scnlog.me/?s=Couplechallenge",
    "Temptation Island VIP": "https://scnlog.me/?s=Temptation%20island%20vip%20german",
    "Sommerhaus": "https://scnlog.me/?s=Sommerhaus",
}

MAX_ITEMS = 5
DATA_FILE = "data.json"

# Alte Daten laden, damit bei Fehlern nichts verloren geht
old_data = {}
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            old_data = json.load(f)
    except Exception:
        old_data = {}

scraper = cloudscraper.create_scraper()
all_data = {}

for category, url in URLS.items():
    try:
        response = scraper.get(url, timeout=20)
        if response.status_code != 200:
            print(f"Fehler bei {category}: HTTP {response.status_code}")
            all_data[category] = old_data.get(category, [])
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        items = []

        for post in soup.select("h2 a, h3 a, .entry-title a"):
            title = post.get_text(strip=True)
            link = post.get("href")

            if not title or not link or "scnlog.me" not in link:
                continue
            if any(item["link"] == link for item in items):
                continue

            items.append({"title": title, "link": link})
            if len(items) >= MAX_ITEMS:
                break

        if items:
            all_data[category] = items
        else:
            # Nichts gefunden (z.B. Seite geblockt) -> alte Einträge behalten
            print(f"Keine Einträge bei {category}, behalte alte Daten.")
            all_data[category] = old_data.get(category, [])

    except Exception as e:
        print(f"Fehler bei {category}: {e}")
        all_data[category] = old_data.get(category, [])

if all_data != old_data:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    print("Neue Einträge gefunden, data.json aktualisiert.")
else:
    print("Keine Änderungen.")
