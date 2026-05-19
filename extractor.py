"""
Extraction des données musicales depuis l'API Last.fm.
Couvre : top tracks, top artistes, infos détaillées, tags/genres.
"""

import os
import json
import time
import logging
from datetime import datetime

import requests

from config import (
    LASTFM_API_KEY,
    LASTFM_BASE_URL,
    RAW_DATA_DIR,
    EXTRACT_LIMIT,
    NB_PAGES,
    COUNTRIES,
    TARGET_TAGS,
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# Client HTTP Last.fm 
def lastfm_get(method: str, params: dict = {}) -> dict | None:
    """
    Appel générique à l'API Last.fm.
    Gère les erreurs HTTP et les réponses vides.
    """
    base_params = {
        "method":  method,
        "api_key": LASTFM_API_KEY,
        "format":  "json",
        "limit":   EXTRACT_LIMIT,
    }
    base_params.update(params)

    try:
        response = requests.get(LASTFM_BASE_URL, params=base_params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            log.error(f"Last.fm error {data['error']} : {data.get('message')}")
            return None

        return data

    except requests.exceptions.RequestException as e:
        log.error(f"Erreur HTTP ({method}) : {e}")
        return None


# Sauvegarde JSON 
def save_raw(data: dict | list, filename: str) -> str:
    """Sauvegarde les données brutes dans data/raw/ avec timestamp."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath  = os.path.join(RAW_DATA_DIR, f"{timestamp}_{filename}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info(f"  -> Sauvegarde : {filepath}")
    return filepath


# Extraction : Top Tracks par pays 
def extract_top_tracks_by_country(country: str) -> list[dict]:
    """Récupère les top tracks pour un pays. Endpoint : geo.getTopTracks"""
    all_tracks = []

    for page in range(1, NB_PAGES + 1):
        data = lastfm_get("geo.getTopTracks", {"country": country, "page": page})
        if not data:
            break
        tracks = data.get("tracks", {}).get("track", [])
        if not tracks:
            break
        for track in tracks:
            track["_country"] = country
        all_tracks.extend(tracks)
        log.info(f"  {country} page {page} : {len(tracks)} tracks")
        time.sleep(0.25)

    return all_tracks


def extract_all_top_tracks() -> list[dict]:
    """Lance l'extraction top tracks pour tous les pays cibles."""
    all_tracks = []
    for country in COUNTRIES:
        log.info(f"Top tracks — {country}")
        all_tracks.extend(extract_top_tracks_by_country(country))
    log.info(f"Total top tracks (pays) : {len(all_tracks)}")
    save_raw(all_tracks, "top_tracks_by_country")
    return all_tracks


# Extraction : Top Tracks par tag/genre 
def extract_top_tracks_by_tag() -> list[dict]:
    """Récupère les top tracks par tag. Endpoint : tag.getTopTracks"""
    all_tracks = []

    for tag in TARGET_TAGS:
        log.info(f"Top tracks — tag : {tag}")
        for page in range(1, NB_PAGES + 1):
            data = lastfm_get("tag.getTopTracks", {"tag": tag, "page": page})
            if not data:
                break
            tracks = data.get("tracks", {}).get("track", [])
            if not tracks:
                break
            for track in tracks:
                track["_tag"] = tag
            all_tracks.extend(tracks)
            log.info(f"  {tag} page {page} : {len(tracks)} tracks")
            time.sleep(0.25)

    log.info(f"Total top tracks (tags) : {len(all_tracks)}")
    save_raw(all_tracks, "top_tracks_by_tag")
    return all_tracks


# Extraction : Top Artistes par pays 
def extract_top_artists_by_country() -> list[dict]:
    """Récupère les top artistes par pays. Endpoint : geo.getTopArtists"""
    all_artists = []

    for country in COUNTRIES:
        log.info(f"Top artistes — {country}")
        for page in range(1, NB_PAGES + 1):
            data = lastfm_get("geo.getTopArtists", {"country": country, "page": page})
            if not data:
                break
            artists = data.get("topartists", {}).get("artist", [])
            if not artists:
                break
            for artist in artists:
                artist["_country"] = country
            all_artists.extend(artists)
            log.info(f"  {country} page {page} : {len(artists)} artistes")
            time.sleep(0.25)

    log.info(f"Total artistes (pays) : {len(all_artists)}")
    save_raw(all_artists, "top_artists_by_country")
    return all_artists


# Extraction : Infos détaillées des tracks 
def extract_track_info(tracks: list[dict]) -> list[dict]:
    """
    Infos détaillées par track : durée, playcount, listeners, tags.
    Endpoint : track.getInfo
    """
    seen, unique = set(), []
    for t in tracks:
        artist = t.get("artist", {})
        artist_name = artist.get("name", "") if isinstance(artist, dict) else str(artist)
        track_name  = t.get("name", "")
        key = (artist_name.lower(), track_name.lower())
        if key not in seen:
            seen.add(key)
            unique.append((artist_name, track_name))

    log.info(f"Infos détaillées pour {len(unique)} tracks uniques")
    detailed = []

    for i, (artist, track) in enumerate(unique):
        data = lastfm_get("track.getInfo", {"artist": artist, "track": track})
        if data and "track" in data:
            detailed.append(data["track"])
        if (i + 1) % 50 == 0:
            log.info(f"  {i + 1}/{len(unique)} tracks traitées")
        time.sleep(0.2)

    log.info(f"Total tracks détaillées : {len(detailed)}")
    save_raw(detailed, "tracks_detailed")
    return detailed


# Extraction : Infos détaillées des artistes 
def extract_artist_info(artists: list[dict]) -> list[dict]:
    """
    Infos détaillées par artiste : bio, tags, listeners, playcount.
    Endpoint : artist.getInfo
    """
    seen, unique = set(), []
    for a in artists:
        name = a.get("name", "")
        if name.lower() not in seen:
            seen.add(name.lower())
            unique.append(name)

    log.info(f"Infos détaillées pour {len(unique)} artistes uniques")
    detailed = []

    for i, artist in enumerate(unique):
        data = lastfm_get("artist.getInfo", {"artist": artist})
        if data and "artist" in data:
            detailed.append(data["artist"])
        if (i + 1) % 25 == 0:
            log.info(f"  {i + 1}/{len(unique)} artistes traités")
        time.sleep(0.2)

    log.info(f"Total artistes détaillés : {len(detailed)}")
    save_raw(detailed, "artists_detailed")
    return detailed


#  Extraction complète 
def run_extraction() -> dict:
    """
    Pipeline d'extraction complet :
    1. Top tracks par pays
    2. Top tracks par tag/genre
    3. Top artistes par pays
    4. Infos détaillées des tracks (200 max)
    5. Infos détaillées des artistes (100 max)
    """
    if not LASTFM_API_KEY:
        raise ValueError("LASTFM_API_KEY manquant dans le fichier .env")

    log.info("=" * 55)
    log.info("  DEMARRAGE EXTRACTION — Music Trends Analytics")
    log.info("  Source : Last.fm API")
    log.info("=" * 55)

    tracks_country = extract_all_top_tracks()
    tracks_tag     = extract_top_tracks_by_tag()
    all_tracks     = tracks_country + tracks_tag

    artists_raw    = extract_top_artists_by_country()
    tracks_detail  = extract_track_info(all_tracks[:200])
    artists_detail = extract_artist_info(artists_raw[:100])

    log.info("=" * 55)
    log.info("  EXTRACTION TERMINEE")
    log.info(f"  Tracks brutes     : {len(all_tracks)}")
    log.info(f"  Tracks détaillées : {len(tracks_detail)}")
    log.info(f"  Artistes bruts    : {len(artists_raw)}")
    log.info(f"  Artistes détaillés: {len(artists_detail)}")
    log.info("=" * 55)

    return {
        "tracks":         all_tracks,
        "tracks_detail":  tracks_detail,
        "artists":        artists_raw,
        "artists_detail": artists_detail,
    }