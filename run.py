import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tidalapi
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# ---------- Configuration ----------
# Spotify credentials (set these as environment variables)
SPOTIFY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")
SPOTIFY_SCOPE = "playlist-read-private"

# Tidal account credentials (use your throwaway email/password)
TIDAL_EMAIL = os.getenv("TIDAL_EMAIL")
TIDAL_PASSWORD = os.getenv("TIDAL_PASSWORD")

# The Spotify playlist ID or URI (set as env var SPOTIFY_PLAYLIST_ID)
PLAYLIST_ID = os.getenv("SPOTIFY_PLAYLIST_ID")

# Download directory and rate limiting
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", os.path.join(os.getcwd(), "downloads"))
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "30"))

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------- Setup Selenium WebDriver ----------
options = webdriver.ChromeOptions()
# To run in headless mode uncomment next line (downloads may require extra setup)
# options.add_argument("--headless")
prefs = {"download.default_directory": DOWNLOAD_DIR}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

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
    session.login(TIDAL_EMAIL, TIDAL_PASSWORD)
    return session


def find_tidal_track(session, title, artist):
    query = f"{title} {artist}"
    result = session.search(query, models=[tidalapi.Track])
    tidal_tracks = result.get('tracks', [])
    if tidal_tracks:
        track = tidal_tracks[0]
        return f"https://tidal.com/browse/track/{track.id}"
    return None

# ---------- DoubleDouble: Automate Download ----------
def download_with_doubledouble(tidal_url):
    driver.get("https://doubledouble.top")
    time.sleep(5)  # wait for page load (adjust if needed)
    # Locate URL input (adjust selector if the site changes)
    input_box = driver.find_element(By.NAME, "url")
    input_box.clear()
    input_box.send_keys(tidal_url)
    # Click the Download button
    download_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Download')]")
    download_btn.click()
    # Wait for download to initiate
    time.sleep(10)

# ---------- Main Workflow ----------
def main():
    spotify_tracks = fetch_spotify_tracks()
    tidal_session = login_tidal()
    not_found = []

    for item in spotify_tracks:
        track = item['track']
        title = track['name']
        artist = track['artists'][0]['name']
        print(f"Processing: {title} – {artist}")

        tidal_url = find_tidal_track(tidal_session, title, artist)
        if tidal_url:
            print(f"  Found on Tidal: {tidal_url}")
            download_with_doubledouble(tidal_url)
            print(f"  Download initiated. Sleeping for {RATE_LIMIT_SECONDS}s...")
            time.sleep(RATE_LIMIT_SECONDS)
        else:
            print(f"  Not found on Tidal. Logging.")
            not_found.append(f"{title} – {artist}")

    # Write not-found tracks to file
    with open("not_found_tracks.txt", "w", encoding="utf-8") as f:
        for entry in not_found:
            f.write(entry + "\n")

    print("Done! See not_found_tracks.txt for any missing songs.")
    driver.quit()

if __name__ == "__main__":
    main()
