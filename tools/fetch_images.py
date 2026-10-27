"""Find a photo for each place (Wikipedia lead image, else a Commons search), keep only freely
licensed Commons files, download a ~1000px thumbnail and record author + licence for credits."""
import json, re, sys, time, html
from pathlib import Path
import requests

OUT = Path(sys.argv[1])          # directory for downloaded files
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "ICDMAI-speaker-guide/1.0 (personal, non-commercial event guide)"}

# key: (wikipedia article, commons search fallback)
PLACES = {
  "lalbagh": ("Lalbagh", "Lalbagh glass house Bangalore"),
  "krmarket": ("K. R. Market", "KR Market flowers Bangalore"),
  "mtr": ("Mavalli Tiffin Rooms", "Mavalli Tiffin Room"),
  "bulltemple": ("Bull Temple", "Bull temple Basavanagudi Nandi"),
  "tipu": ("Tipu Sultan's Summer Palace", "Tipu Sultan summer palace Bangalore"),
  "vvpuram": (None, "VV Puram food street"),
  "cubbon": ("Vidhana Soudha", "Vidhana Soudha"),
  "vitm": ("Visvesvaraya Industrial & Technological Museum", "Visvesvaraya Industrial Technological Museum"),
  "map": ("Museum of Art & Photography", "Museum of Art and Photography Bengaluru"),
  "ngma": ("National Gallery of Modern Art, Bangalore", "National Gallery of Modern Art Bangalore"),
  "palace": ("Bangalore Palace", "Bangalore Palace"),
  "commercial": ("Commercial Street, Bangalore", "Commercial Street Bangalore"),
  "churchst": ("Church Street, Bangalore", "Church Street Bangalore"),
  "iskcon": ("ISKCON Temple Bangalore", "ISKCON temple Bangalore"),
  "malleshwaram": ("Kadu Malleshwara Temple", "Kadu Malleshwara temple"),
  "sankey": ("Sankey Tank", "Sankey tank"),
  "koramangala": ("Koramangala", "Koramangala"),
  "indiranagar": (None, "Indiranagar Bangalore restaurant night"),
  "rangashankara": ("Ranga Shankara", "Ranga Shankara theatre"),
  "bannerghatta": ("Bannerghatta Biological Park", "Bannerghatta tiger safari"),
  "nandi": ("Nandi Hills, India", "Nandi Hills sunrise"),
  "srirangapatna": ("Srirangapatna", "Daria Daulat Bagh Srirangapatna"),
  "mysorepalace": ("Mysore Palace", "Mysore Palace"),
  "chamundi": ("Chamundeshwari Temple", "Chamundeshwari temple Mysore gopuram"),
  "venue": ("Christ University", "Christ University Bangalore campus"),
  "cubbonpark": ("Cubbon Park", "Cubbon Park Bangalore"),
  "stay_mg": ("Mahatma Gandhi Road, Bangalore", "MG Road Bangalore"),
  "stay_jayanagar": ("Jayanagar", "Jayanagar Bangalore"),
  "stay_richmond": ("Richmond Town", "Richmond Town Bangalore"),
  "stay_whitefield": ("Whitefield, Bangalore", "Whitefield Bangalore"),
  "stay_hosur": ("Forum Mall, Bangalore", "Forum mall Koramangala"),
}
FREE = re.compile(r"(CC[ -]BY|CC0|Public domain|PD|GFDL)", re.I)
strip = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

def api(url, params):
    for attempt in range(6):
        r = requests.get(url, headers=UA, timeout=30, params={**params, "format": "json"})
        if r.status_code == 200 and r.text.strip().startswith("{"):
            return r.json()
        time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"API failed: HTTP {r.status_code}")

def commons_info(name):
    r = api("https://commons.wikimedia.org/w/api.php", {"action": "query", "titles": "File:" + name,
            "prop": "imageinfo", "iiprop": "url|extmetadata|mime", "iiurlwidth": 1000})
    p = next(iter(r["query"]["pages"].values()))
    if "imageinfo" not in p: return None
    ii = p["imageinfo"][0]; em = ii.get("extmetadata", {})
    lic = strip(em.get("LicenseShortName", {}).get("value"))
    if not FREE.search(lic) or ii.get("mime") not in ("image/jpeg", "image/png", "image/webp"): return None
    return ii, em, lic

def search_names(q):
    r = api("https://commons.wikimedia.org/w/api.php", {"action": "query", "list": "search",
            "srsearch": q + " filetype:bitmap", "srnamespace": 6, "srlimit": 6})
    return [h["title"].split(":", 1)[1] for h in r["query"]["search"]]

cred_path = OUT / "credits.json"
meta = json.loads(cred_path.read_text(encoding="utf-8")) if cred_path.exists() else {}
for key, (title, query) in PLACES.items():
    if key in meta: print(f"{key}: already have"); continue
    try:
        names = []
        if title:
            r = api("https://en.wikipedia.org/w/api.php", {"action": "query", "redirects": 1, "titles": title,
                    "prop": "pageimages", "piprop": "name"})
            n = next(iter(r["query"]["pages"].values())).get("pageimage")
            if n: names.append(n)
        names += search_names(query)
        got = None
        for n in names:
            if re.search(r"logo|map|seal|emblem|\.svg", n, re.I): continue
            info = commons_info(n); time.sleep(1)
            if info: got = (n, *info); break
        if not got: print(f"{key}: nothing usable"); continue
        n, ii, em, lic = got
        img = None
        for attempt in range(5):
            img = requests.get(ii["thumburl"], headers=UA, timeout=60)
            if img.status_code == 200: break
            time.sleep(5 * (attempt + 1))
        img.raise_for_status()
        ext = ".png" if ii["mime"] == "image/png" else ".jpg"
        (OUT / (key + ext)).write_bytes(img.content)
        meta[key] = {"file": key + ext, "title": n, "author": strip(em.get("Artist", {}).get("value"))[:80],
                     "license": lic, "page": ii["descriptionurl"]}
        cred_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{key}: OK {n} [{lic}] {len(img.content)//1024} KB")
        time.sleep(2)
    except Exception as e:
        print(f"{key}: error {e}")
