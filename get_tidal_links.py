import os
import csv
import spotipy
import tidalapi
import webbrowser
from spotipy.oauth2 import SpotifyOAuth

# ── Configuration ────────────────────────────────────────────────────
SPOTIFY_CLIENT_ID     = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI  = os.getenv("SPOTIPY_REDIRECT_URI")
SPOTIFY_SCOPE         = "playlist-read-private"

# Paste your playlist link or ID here:
raw_playlist = "https://open.spotify.com/playlist/5epr9yWDpDeQ88iirjoEjG?si=27a32f8107b34cbd"
PLAYLIST_ID = raw_playlist.split("?", 1)[0]

# ── Spotify: Fetch Playlist Tracks ───────────────────────────────────
def fetch_spotify_tracks():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id     = SPOTIFY_CLIENT_ID,
        client_secret = SPOTIFY_CLIENT_SECRET,
        redirect_uri  = SPOTIFY_REDIRECT_URI,
        scope         = SPOTIFY_SCOPE
    ))
    all_tracks = []
    results = sp.playlist_tracks(PLAYLIST_ID)
    all_tracks.extend(results["items"])
    while results["next"]:
        results = sp.next(results)
        all_tracks.extend(results["items"])
    return all_tracks

# ── Tidal: OAuth login & search ──────────────────────────────────────
def login_tidal():
    session = tidalapi.Session()
    login, future = session.login_oauth()
    webbrowser.open(login.verification_uri_complete)
    print(f"\n→ Complete Tidal login here: {login.verification_uri_complete}\n")
    future.result()
    if not session.check_login():
        raise RuntimeError("❌ Tidal OAuth failed")
    print("✅ Logged into Tidal\n")
    return session


def find_tidal_track(session, title, artist):
    query = f"{title} {artist}"
    search = session.search(query, models=[tidalapi.Track])
    tracks = search.get("tracks", [])
    if not tracks:
        return None
    for track in tracks:
        if artist.lower() in track.artist.name.lower():
            return track, f"https://tidal.com/browse/track/{track.id}"
    return None

# ── Main ──────────────────────────────────────────────────────────────
def main():
    print("🔍 Fetching Spotify playlist…")
    spotify_items = fetch_spotify_tracks()
    print(f"  ▶️  Found {len(spotify_items)} tracks\n")

    tidal_session = login_tidal()

    output_rows = []
    not_found = []

    print("🔍 Searching on Tidal…")
    for item in spotify_items:
        sp_track = item["track"]
        sp_title  = sp_track["name"]
        sp_artist = sp_track["artists"][0]["name"]
        print(f"• {sp_title} — {sp_artist}", end="  ")

        result = find_tidal_track(tidal_session, sp_title, sp_artist)
        if result:
            tidal_track, tidal_url = result
            td_title  = tidal_track.name
            td_artist = tidal_track.artist.name
            print(f"→ {td_title} — {td_artist}")
            # collect row data
            output_rows.append([
                sp_artist,
                td_artist,
                sp_title,
                td_title,
                tidal_url
            ])
        else:
            print("→ ❌ Not found")
            not_found.append(f"{sp_title} — {sp_artist}")

    # write the full info CSV
    with open("tidal_links.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Spotify Artist", "Tidal Artist", "Spotify Title", "Tidal Title", "Tidal URL"])
        writer.writerows(output_rows)

    # write not-found
    with open("not_found_tracks.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(not_found))

    print(f"\n✅ Done!  {len(output_rows)} found, {len(not_found)} missing.")
    print(" • Full info → tidal_links.csv")
    print(" • URLs only  → tidal_links.txt")
    print(" • Missing    → not_found_tracks.txt")

if __name__ == "__main__":
    main()
