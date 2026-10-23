from datetime import datetime, timedelta, timezone
import json
import os
import re
from bs4 import BeautifulSoup
import cloudscraper

URLS = {
    "Are You The One": "https://scnlog.me/?s=are%20you%20the%20one%20reality",
    "Love Island VIP": "https://scnlog.me/?s=Love%20island%20vip%20german",
    "CoupleChallenge": "https://scnlog.me/?s=Couplechallenge",
    "Temptation Island VIP": "https://scnlog.me/?s=Temptation%20island%20vip%20german",
    "Sommerhaus": "https://scnlog.me/?s=Sommerhaus",
    "Der Promihof": "https://scnlog.me/?s=Der%20Promihof"
}

MAX_ITEMS = 5
DATA_FILE = "data.json"

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

cutoff_date = datetime.now() - timedelta(days=2)
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

        # 1. Datum & Uhrzeit aus der Übersicht ermitteln
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

        berlin_item_time = datetime.now(timezone.utc) + timedelta(hours=2)
        item_datetime_str = dt.strftime("%Y-%m-%d %H:%M") if dt else berlin_item_time.strftime("%Y-%m-%d %H:%M")

        # 2. Detailseite aufrufen, um die Download-Links (MultiUp etc.) zu finden
        download_links = []
        try:
          detail_resp = scraper.get(detail_link, timeout=10)
          if detail_resp.status_code == 200:
            detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
            # Alle Links auf der Detailseite durchsuchen
            for link_tag in detail_soup.find_all("a", href=True):
              href = link_tag["href"]
              # Nach typischen Hostern oder direkt MultiUp filtern
              if any(h in href.lower() for h in ["multiup.io", "ddownload.com", "nitroflare.com"]):
                if href not in download_links:
                  download_links.append(href)
            
            # Falls im Textblock (z.B. <pre> oder Code-Bereich) Links stehen
            for code_tag in detail_soup.find_all(["pre", "code", "div"]):
              code_text = code_tag.get_text()
              found_urls = re.findall(r'https?://[^\s<>"]+', code_text)
              for url_item in found_urls:
                if any(h in url_item.lower() for h in ["multiup.io", "ddownload.com", "nitroflare.com"]):
                  if url_item not in download_links:
                    download_links.append(url_item)
        except Exception as e:
          print(f"Fehler beim Laden der Detailseite {detail_link}: {e}")

        # Primärer MultiUp-Link (falls vorhanden, sonst der erste gefundene Link oder Fallback auf Detailseite)
        multiup_link = next((l for l in download_links if "multiup.io" in l), detail_link)

        if not any(item["title"] == title for item in items):
          items.append({
              "title": title,
              "link": detail_link,
              "multiup": multiup_link,
              "all_links": download_links,
              "datetime": item_datetime_str
          })

      if len(items) >= MAX_ITEMS:
        break

    all_data[category] = items

  except Exception as e:
    print(f"Fehler bei {category}: {e}")
    all_data[category] = old_data.get(category, [])

berlin_now = datetime.now(timezone.utc) + timedelta(hours=2)
output_structure = {
    "last_updated": berlin_now.strftime("%Y-%m-%d %H:%M"),
    "categories": all_data
}

with open(DATA_FILE, "w", encoding="utf-8") as f:
  json.dump(output_structure, f, ensure_ascii=False, indent=4)

print("Scraping beendet und data.json aktualisiert.")
