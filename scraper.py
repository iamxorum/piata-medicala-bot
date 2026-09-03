import re
import unicodedata

import requests
from bs4 import BeautifulSoup

CATEGORY_URL = "https://www.piatamedicala.ro/locuri-de-munca-2/oferte-stomatologie-4-1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def strip_diacritics(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c)).lower()


def fetch_page(page_number: int) -> str:
    url = CATEGORY_URL if page_number == 1 else f"{CATEGORY_URL}?pagina={page_number}"
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.text


def _meta_field(li_tag, icon_class: str) -> str:
    if not li_tag.find("i", class_=icon_class):
        return ""
    text = li_tag.get_text(" ", strip=True)
    return text.split(":", 1)[1].strip() if ":" in text else text.strip()


def parse_ads(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    ads = []
    for ad_div in soup.select("div.anunt"):
        link_tag = ad_div.select_one("h3[itemprop=name] a")
        if not link_tag or not link_tag.get("href"):
            continue

        match = re.search(r"/anunt/(\d+)-", link_tag["href"])
        if not match:
            continue

        location = ""
        date = ""
        for li in ad_div.select("ul.anunt__meta li"):
            if li.find("i", class_="fa-location-dot"):
                location = _meta_field(li, "fa-location-dot")
            elif li.find("i", class_="fa-calendar"):
                date = _meta_field(li, "fa-calendar")

        ads.append({
            "id": match.group(1),
            "title": link_tag.get_text(strip=True),
            "url": f"https://www.piatamedicala.ro{link_tag['href']}",
            "location": location,
            "date": date,
        })
    return ads


def fetch_matching_ads(config: dict) -> list[dict]:
    all_ads = []
    for page in range(1, config["pages_to_check"] + 1):
        try:
            html = fetch_page(page)
        except requests.RequestException:
            if page == 1:
                raise 
            print(f"Eroare la pagina {page}, continui cu ce am gasit pana acum.")
            break
        page_ads = parse_ads(html)
        if not page_ads:
            break
        all_ads.extend(page_ads)

    return [ad for ad in all_ads if _matches_filters(ad, config)]


def _matches_filters(ad: dict, config: dict) -> bool:
    title = strip_diacritics(ad["title"])
    location = strip_diacritics(ad["location"])

    if not any(kw in title for kw in config["include_keywords"]):
        return False
    if any(kw in title for kw in config["exclude_keywords"]):
        return False
    if not any(kw in location for kw in config["location_keywords"]):
        return False
    return True
