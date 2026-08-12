#!/usr/bin/env python3
"""CINEMASH catalog builder — TMDB discover + IMDb datasets -> catalog.json
Criteria: movie type only, >=60 min, IMDb rating >=6.0, votes >=1000,
rolling 50-year window (200 quarters), Bollywood hi/IN + Hollywood en/US."""
import csv, gzip, io, json, os, sys, time, urllib.request
from datetime import date

TMDB = "https://api.themoviedb.org/3"
KEY = None
for line in open(os.path.join(os.path.dirname(__file__) or ".", ".env")):
    if line.startswith("TMDB_API_KEY="):
        KEY = line.split("=", 1)[1].strip()
if not KEY:
    sys.exit("TMDB_API_KEY missing in .env")

def quarter_window(today=None):
    """Start of (current quarter - 200 quarters) -> today."""
    t = today or date.today()
    q0 = (t.month - 1) // 3          # 0-based current quarter
    total = t.year * 4 + q0 - 200
    y, q = divmod(total, 4)
    return date(y, q * 3 + 1, 1), t

def tmdb(path, **params):
    params["api_key"] = KEY
    url = TMDB + path + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 ** attempt)
    raise RuntimeError("TMDB failed: " + path)

def discover(country, lang, gte, lte):
    out, page, total = [], 1, 1
    while page <= total and page <= 500:
        d = tmdb("/discover/movie", with_origin_country=country,
                 with_original_language=lang, sort_by="popularity.desc",
                 include_adult="false", include_video="false",
                 **{"primary_release_date.gte": gte, "primary_release_date.lte": lte,
                    "vote_count.gte": 20, "page": page})
        total = d.get("total_pages", 1)
        out += d.get("results", [])
        page += 1
        time.sleep(0.05)
    return out

def imdb_maps():
    """Stream IMDb basics+ratings; return {tconst: (year, runtime_ok, is_movie, genres)} and ratings."""
    def fetch(name):
        url = f"https://datasets.imdbws.com/{name}"
        print("downloading", name, "...")
        return gzip.open(io.BytesIO(urllib.request.urlopen(url).read()), "rt", encoding="utf-8")
    ratings = {}
    for row in csv.reader(fetch("title.ratings.tsv.gz"), delimiter="\t"):
        if row[0] == "tconst": continue
        try: ratings[row[0]] = (float(row[1]), int(row[2]))
        except ValueError: pass
    basics = {}
    for row in csv.reader(fetch("title.basics.tsv.gz"), delimiter="\t"):
        if row[0] == "tconst" or row[1] != "movie": continue  # excludes tvMovie/short/series/video/game etc.
        tc = row[0]
        r = ratings.get(tc)
        if not r or r[0] < 6.0 or r[1] < 1000: continue
        try: run_ok = int(row[7]) >= 60
        except ValueError: run_ok = False
        if not run_ok: continue
        basics[tc] = (row[3], row[8])  # startYear, genres
    return basics, ratings

def tier(votes, rating):
    if votes >= 100000 or (votes >= 50000 and rating >= 7.5): return "E"
    if votes >= 15000: return "M"
    return "H"

def credits_for(mid):
    c = tmdb(f"/movie/{mid}/credits")
    cast = sorted(c.get("cast", []), key=lambda x: x.get("order", 99))
    hero = next((p["name"] for p in cast if p.get("gender") == 2), None)
    her = next((p["name"] for p in cast if p.get("gender") == 1), None)
    dirn = next((p["name"] for p in c.get("crew", []) if p.get("job") == "Director"), None)
    return hero, her, dirn

def main():
    gte, lte = quarter_window()
    print("window:", gte, "->", lte)
    basics, ratings = imdb_maps()
    dialogues = {}
    dpath = os.path.join(os.path.dirname(__file__) or ".", "dialogues.json")
    if os.path.exists(dpath):
        dialogues = {k: v for k, v in json.load(open(dpath)).items() if not k.startswith("_")}
    movies, seen = [], set()
    for ind, country, lang in (("B", "IN", "hi"), ("H", "US", "en")):
        cands = discover(country, lang, gte.isoformat(), lte.isoformat())
        print(ind, "candidates:", len(cands))
        for m in cands:
            ext = tmdb(f"/movie/{m['id']}/external_ids")
            tc = ext.get("imdb_id")
            if not tc or tc in seen or tc not in basics: continue
            seen.add(tc)
            rating, votes = ratings[tc]
            year, genres = basics[tc]
            hero, her, dirn = credits_for(m["id"])
            movies.append({
                "t": m["title"].upper(), "i": ind,
                "y": int(year) if year.isdigit() else int(m.get("release_date", "0000")[:4]),
                "g": [g for g in genres.split(",") if g and g != r"\N"],
                "d": tier(votes, rating), "hero": hero, "her": her, "dir": dirn,
                "line": dialogues.get(tc, ""), "id": tc,
            })
            time.sleep(0.05)
        print(ind, "kept:", sum(1 for x in movies if x["i"] == ind))
    out = {"generated": date.today().isoformat(),
           "window": {"from": gte.isoformat(), "to": lte.isoformat()},
           "count": len(movies), "movies": movies}
    with open("catalog.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote catalog.json:", len(movies), "movies")

if __name__ == "__main__":
    main()
