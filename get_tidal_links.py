import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tidalapi
import webbrowser

# ---------- Configuration ----------
# Spotify credentials (set these as environment variables)
SPOTIFY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SPOTIFY_SCOPE = "playlist-read-private"

# The Spotify playlist ID or URI (set as env var SPOTIFY_PLAYLIST_ID)
# PLAYLIST_ID = os.getenv("SPOTIFY_PLAYLIST_ID")
# suppose user pasted the share URL or ID+query
raw = "https://open.spotify.com/playlist/0VZ0enNabwuwwHY2rfzSKv?si=01415048a90643e8"
PLAYLIST_ID = raw.split("?", 1)[0]

# ---------- Spotify: Fetch Playlist Tracks ----------
def fetch_spotify_tracks():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPE
    ))
    tracks = []
    results = sp.playlist_tracks(PLAYLIST_ID)
    tracks.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

# ---------- Tidal: Login & Search ----------
def login_tidal():
    session = tidalapi.Session()
    # Initiate the OAuth login process
    login, future = session.login_oauth()
    # Open the verification URL in the default web browser
    webbrowser.open(login.verification_uri_complete)
    print(f"Please complete the login in your browser: {login.verification_uri_complete}")
    # Wait for the user to complete the login
    future.result()
    if not session.check_login():
        raise RuntimeError("TIDAL login failed")
    return session

def find_tidal_track(session, title, artist):
    query = f"{title} {artist}"
    result = session.search(query, models=[tidalapi.Track])
    tidal_tracks = result.get('tracks', [])
    if tidal_tracks:
        track = tidal_tracks[0]
        return f"https://tidal.com/browse/track/{track.id}"
    return None

# ---------- Main Function ----------
def main():
    print("Fetching Spotify playlist tracks...")
    spotify_tracks = fetch_spotify_tracks()
    print(f"Found {len(spotify_tracks)} tracks in playlist")
    
    print("Logging into Tidal...")
    tidal_session = login_tidal()
    
    tidal_links = []
    not_found = []

    print("Searching for tracks on Tidal...")
    for item in spotify_tracks:
        track = item['track']
        title = track['name']
        artist = track['artists'][0]['name']
        print(f"Processing: {title} – {artist}")

        tidal_url = find_tidal_track(tidal_session, title, artist)
        if tidal_url:
            print(f"  Found on Tidal: {tidal_url}")
            tidal_links.append(tidal_url)
        else:
            print(f"  Not found on Tidal. Logging.")
            not_found.append(f"{title} – {artist}")

    # Save tidal links to file
    with open("tidal_links.txt", "w", encoding="utf-8") as f:
        for link in tidal_links:
            f.write(link + "\n")

    # Save not found tracks to file
    with open("not_found_tracks.txt", "w", encoding="utf-8") as f:
        for entry in not_found:
            f.write(entry + "\n")

    print(f"\nDone! Found {len(tidal_links)} tracks on Tidal.")
    print(f"Tidal links saved to: tidal_links.txt")
    print(f"Not found tracks saved to: not_found_tracks.txt")

if __name__ == "__main__":
    main()
