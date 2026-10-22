from datetime import datetime
import json
import os
import cloudscraper
from bs4 import BeautifulSoup

URLS = {
    "Are You The One": "https://scnlog.me/?s=are%20you%20the%20one%20reality",
    "Love Island VIP": "https://scnlog.me/?s=Love%20island%20vip%20german",
    "CoupleChallenge": "https://scnlog.me/?s=Couplechallenge",
    "Temptation Island VIP": (
        "https://scnlog.me/?s=Temptation%20island%20vip%20german"
    ),
    "Sommerhaus": "https://scnlog.me/?s=Sommerhaus",
}

MAX_ITEMS = 5
DATA_FILE = "data.json"
TODAY_DATE = datetime.now().strftime("%Y-%m-%d")  # Heutiges Datum (z.B. "2026-10-23")

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

    for a in soup.find_all("a", href=True):
      title = a.get_text(strip=True)
      link = a["href"]

      if not title or "German" in title and len(title) < 15:
        continue
      if not link or "scnlog.me" not in link:
        continue

      if (
          "GERMAN" in title.upper()
          or "S0" in title.upper()
          or "STAFFEL" in title.upper()
      ):
        if link.startswith("/"):
          link = "https://scnlog.me" + link

        # Prüfen, ob der Eintrag bereits in den alten Daten existiert (um das ursprüngliche Datum beizubehalten)
        existing_date = TODAY_DATE
        for old_item in old_data.get(category, []):
          if old_item["link"] == link:
            existing_date = old_item.get("date", TODAY_DATE)
            break

        if not any(item["link"] == link for item in items):
          items.append(
              {"title": title, "link": link, "date": existing_date}
          )

      if len(items) >= MAX_ITEMS:
        break

    if items:
      all_data[category] = items
    else:
      all_data[category] = old_data.get(category, [])

  except Exception as e:
    print(f"Fehler bei {category}: {e}")
    all_data[category] = old_data.get(category, [])

with open(DATA_FILE, "w", encoding="utf-8") as f:
  json.dump(all_data, f, ensure_ascii=False, indent=4)

print("Scraping beendet und data.json aktualisiert.")
