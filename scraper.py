from datetime import datetime
import json
import os
import re
from bs4 import BeautifulSoup
import cloudscraper

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

old_data = {}
if os.path.exists(DATA_FILE):
  try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      old_data = json.load(f)
  except Exception:
    old_data = {}

scraper = cloudscraper.create_scraper()
all_data = {}

months_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}"
time_pattern = r"\d{2}:\d{2}"


def parse_scnlog_datetime(date_str, time_str):
  try:
    # Entfernt Endungen wie 'st', 'nd', 'rd', 'th' (z.B. "22nd" -> "22")
    clean_date = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str)
    full_str = f"{clean_date} {time_str}"
    dt = datetime.strptime(full_str.strip(), "%B %d, %Y %H:%M")
    return dt.strftime("%Y-%m-%d %H:%M")
  except Exception:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


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

        # Container / Zeile des Eintrags finden, um Datum & Uhrzeit auszulesen
        container = a.find_parent("div")
        container_text = container.get_text() if container else ""

        date_match = re.search(months_pattern, container_text)
        time_match = re.search(time_pattern, container_text)

        date_str = date_match.group(0) if date_match else ""
        time_str = time_match.group(0) if time_match else "00:00"

        item_datetime = (
            parse_scnlog_datetime(date_str, time_str)
            if date_str
            else datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        if not any(item["link"] == link for item in items):
          items.append(
              {"title": title, "link": link, "datetime": item_datetime}
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
