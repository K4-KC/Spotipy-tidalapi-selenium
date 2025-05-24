import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tidalapi
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import webbrowser

# Point to your Brave browser executable:
brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

# ---------- Configuration ----------
# Spotify credentials (set these as environment variables)
SPOTIFY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SPOTIFY_SCOPE = "playlist-read-private"

# Tidal account credentials (use your throwaway email/password)
TIDAL_EMAIL = os.getenv("TIDAL_EMAIL")
TIDAL_PASSWORD = os.getenv("TIDAL_PASSWORD")

# The Spotify playlist ID or URI (set as env var SPOTIFY_PLAYLIST_ID)
# PLAYLIST_ID = os.getenv("SPOTIFY_PLAYLIST_ID")
# suppose user pasted the share URL or ID+query
raw = "https://open.spotify.com/playlist/0VZ0enNabwuwwHY2rfzSKv?si=01415048a90643e8"
PLAYLIST_ID = raw.split("?", 1)[0]

# Download directory and rate limiting
# Replace with hard-coded values instead of environment variables:
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
RATE_LIMIT_SECONDS = 30  # seconds to wait between downloads

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
print(f"Downloads will be saved to: {DOWNLOAD_DIR}")

# ---------- Setup Selenium WebDriver ----------
options = webdriver.ChromeOptions()
# To run in headless mode uncomment next line (downloads may require extra setup)
# options.add_argument("--headless")
# Set Chrome download directory
# options.binary_location = brave_path # Removed this line
prefs = {"download.default_directory": DOWNLOAD_DIR}
options.add_experimental_option("prefs", prefs)

# Disable extensions and other settings that might cause issues
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--enable-logging")
options.add_argument("--log-level=0")

# Use a separate user data directory for automation to avoid conflicts with running Chrome
# This allows us to have persistent sessions while not interfering with your main Chrome
automation_user_data = os.path.join(os.path.expanduser("~"), "ChromeAutomation")
options.add_argument(f"--user-data-dir={automation_user_data}")
options.add_argument("--profile-directory=Default")

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("Chrome opened successfully with automation profile.")
    print("You can now sign into any accounts you need in this browser window.")
    print("This profile will persist between script runs.")
except Exception as e:
    print(f"Error initializing Chrome WebDriver: {e}")
    print("Tips to fix:")
    print("1. Make sure Chrome browser is not already running")
    print("2. Check if Chrome browser is installed")
    print("3. Try running the script with administrator privileges")
    exit(1)

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

# ---------- DoubleDouble: Automate Download ----------
def download_with_doubledouble(tidal_url):
    driver.get("https://doubledouble.top")

    # 1) Wait up to 20s for the #dl-input element to appear
    input_box = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "dl-input"))
    )

    # 2) Paste the Tidal URL into that input
    input_box.clear()
    time.sleep(2)
    input_box.send_keys(tidal_url)
    time.sleep(2)

    # 3) Click the button with ID dl-button
    download_btn = driver.find_element(By.ID, "dl-button")
    download_btn.click()

    # 4) Give it a moment to start the download
    time.sleep(RATE_LIMIT_SECONDS)

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

    with open("not_found_tracks.txt", "w", encoding="utf-8") as f:
        for entry in not_found:
            f.write(entry + "\n")

    print("Done! See not_found_tracks.txt for any missing songs.")
    driver.quit()

if __name__ == "__main__":
    main()
