import json
import os
import cloudscraper
from bs4 import BeautifulSoup

URLS = {
    "Are You The One": "https://scnlog.me/?s=are%20you%20the%20one%20reality",
    "Love Island VIP": "https://scnlog.me/?s=Love%20island%20vip%20german",
    "CoupleChallenge": "https://scnlog.me/?s=Couplechallenge",
    "Temptation Island VIP": "https://scnlog.me/?s=Temptation%20island%20vip%20german",
    "Sommerhaus": "https://scnlog.me/?s=Sommerhaus"
}

MAX_ITEMS = 5
DATA_FILE = "data.json"

# Alte Daten laden, damit bei einem Fehler nichts überschrieben wird
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

        # Durchsuche alle Links nach typischen Release-Namen (enthalten Punkte und oft 'GERMAN' oder S01-S99)
        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            link = a["href"]

            # Filter für gültige Release-Einträge im neuen Design
            if title and len(title) > 10 and "." in title:
                # Prüfen, ob es ein Link zum Beitrag ist (enthält meistens Bindestriche oder S01E01 etc.)
                if "GERMAN" in title.upper() or "S0" in title.upper() or "STAFFEL" in title.upper():
                    # Absolute URL erzeugen, falls relativ
                    if link.startswith("/"):
                        link = "https://scnlog.me" + link
                    elif not link.startswith("http"):
                        continue

                    # Duplikate in dieser Kategorie vermeiden
                    if not any(item["link"] == link for item in items):
                        items.append({"title": title, "link": link})
                
                if len(items) >= MAX_ITEMS:
                    break

        if items:
            all_data[category] = items
            print(f"{category}: {len(items)} Einträge gefunden.")
        else:
            print(f"Keine Einträge bei {category} gefunden, behalte alte Daten.")
            all_data[category] = old_data.get(category, [])

    except Exception as e:
        print(f"Fehler bei {category}: {e}")
        all_data[category] = old_data.get(category, [])

# Speichern der data.json im Hauptverzeichnis
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=4)

print("Scraping beendet und data.json aktualisiert.")
