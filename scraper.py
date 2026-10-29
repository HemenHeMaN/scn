from datetime import datetime, timedelta
import json
import os
import re
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
import cloudscraper

MAX_ITEMS = 5
DATA_FILE = "data.json"
SHOWS_FILE = "shows.txt"

# Shows dynamisch aus der shows.txt einlesen
URLS = {}
if os.path.exists(SHOWS_FILE):
  try:
    with open(SHOWS_FILE, "r", encoding="utf-8") as f:
      for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
          continue
        if "|" in line:
          parts = line.split("|", 1)
          show_name = parts[0].strip()
          show_url = parts[1].strip()
          URLS[show_name] = show_url
  except Exception as e:
    print(f"Fehler beim Lesen der {SHOWS_FILE}: {e}")

old_data = {}
if os.path.exists(DATA_FILE):
  try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      loaded = json.load(f)
      old_data = loaded.get("categories", loaded)
  except Exception:
    old_data = {}

scraper = cloudscraper.create_scraper()
all_data = {}

months_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}"
time_pattern = r"\b\d{1,2}:\d{2}\b"

def parse_scnlog_datetime(date_str, time_str):
  try:
    clean_date = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str)
    full_str = f"{clean_date} {time_str}"
    dt = datetime.strptime(full_str.strip(), "%B %d, %Y %H:%M")
    return dt
  except Exception:
    return None

cutoff_date = datetime.now() - timedelta(days=4)
cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)

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
      detail_link = a["href"]

      if not title or ("German" in title and len(title) < 15):
        continue
      if not detail_link or "scnlog.me" not in detail_link:
        continue

      if "GERMAN" in title.upper() or "S0" in title.upper() or "STAFFEL" in title.upper():
        if detail_link.startswith("/"):
          detail_link = "https://scnlog.me" + detail_link

        row_container = a
        for _ in range(5):
          if row_container.parent:
            row_container = row_container.parent
            text_block = row_container.get_text(separator=" ")
            if re.search(months_pattern, text_block):
              break

        text_block = row_container.get_text(separator=" ")
        date_match = re.search(months_pattern, text_block)
        time_match = re.search(time_pattern, text_block)

        date_str = date_match.group(0) if date_match else ""
        time_str = time_match.group(0) if time_match else "00:00"

        dt = parse_scnlog_datetime(date_str, time_str)
        if dt and dt < cutoff_date:
          continue

        berlin_item_time = datetime.now(ZoneInfo("Europe/Berlin"))
        item_datetime_str = dt.strftime("%d.%m.%Y %H:%M") if dt else berlin_item_time.strftime("%d.%m.%Y %H:%M")

        download_links = []
        try:
          detail_resp = scraper.get(detail_link, timeout=10)
          if detail_resp.status_code == 200:
            detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
            for tag in detail_soup.find_all(["a", "pre", "code", "div"]):
              text_to_check = tag.get("href", "") + " " + tag.get_text()
              found_urls = re.findall(r'https?://[^\s<>"]+', text_to_check)
              for url_item in found_urls:
                if any(h in url_item.lower() for h in ["multiup.io", "ddownload.com", "nitroflare.com"]):
                  clean_url = url_item.rstrip(".,;:)'\"]")
                  if clean_url not in download_links:
                    download_links.append(clean_url)
        except Exception as e:
          print(f"Fehler beim Laden der Detailseite {detail_link}: {e}")

        multiup_link = next((l for l in download_links if "multiup.io" in l), None)
        if not multiup_link and download_links:
          multiup_link = download_links[0]
        if not multiup_link:
          multiup_link = detail_link

        if not any(item["title"] == title for item in items):
          items.append({
              "title": title,
              "link": detail_link,
              "multiup": multiup_link,
              "datetime": item_datetime_str,
              "_raw_dt": dt if dt else berlin_item_time
          })

      if len(items) >= MAX_ITEMS:
        break

    # 1. Einträge innerhalb der Show nach Datum sortieren (neueste zuerst)
    items.sort(key=lambda x: x["_raw_dt"], reverse=True)

    for item in items:
      item.pop("_raw_dt", None)

    all_data[category] = items

  except Exception as e:
    print(f"Fehler bei {category}: {e}")
    all_data[category] = old_data.get(category, [])

# 2. NEU: Kategorien so sortieren, dass Shows mit Einträgen OBERHALB stehen 
# (nach dem Datum ihres allerneuesten Eintrags) und leere Shows ganz UNTEN landen.
sorted_categories = dict(
    sorted(
        all_data.items(),
        key=lambda item: (
            len(item[1]) > 0,  # True (hat Einträge) kommt vor False (leer)
            item[1][0]["datetime"] if len(item[1]) > 0 else ""  # Neuestes Datum als Unterkriterium
        ),
        reverse=True
    )
)

berlin_now = datetime.now(ZoneInfo("Europe/Berlin"))
output_structure = {
    "last_updated": berlin_now.strftime("%d.%m.%Y %H:%M"),
    "categories": sorted_categories
}

with open(DATA_FILE, "w", encoding="utf-8") as f:
  json.dump(output_structure, f, ensure_ascii=False, indent=4)

print("Scraping beendet und data.json perfekt sortiert aktualisiert.")
