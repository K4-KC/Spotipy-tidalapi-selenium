import os
import time
import tempfile
import shutil
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

# -------- Configuration --------
# Spotify credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SPOTIFY_SCOPE = "playlist-read-private"

# Spotify playlist (hard-coded for demo)
raw = "https://open.spotify.com/playlist/0VZ0enNabwuwwHY2rfzSKv?si=01415048a90643e8"
PLAYLIST_ID = raw.split("?", 1)[0]

# Download settings
download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
RATE_LIMIT = 30  # seconds between downloads
os.makedirs(download_dir, exist_ok=True)

# -------- Selenium Setup --------
# Use the existing Chrome user data directory to retain signed-in session
chrome_user_data = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data")

options = webdriver.ChromeOptions()
options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
options.add_argument(f"--user-data-dir={chrome_user_data}")  # use existing logged-in profile
options.add_argument("--profile-directory=Default")
options.add_argument("--start-maximized")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_experimental_option("prefs", {"download.default_directory": download_dir})
# Turn off automation flags
options.add_experimental_option("excludeSwitches", ["enable-automation"])  
options.add_experimental_option("useAutomationExtension", False)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# -------- Spotify Fetch --------
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
    while results.get('next'):
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

# -------- Tidal Login --------
def login_tidal():
    session = tidalapi.Session()
    # First attempt
    login, future = session.login_oauth()
    webbrowser.open(login.verification_uri_complete)
    print("Please complete TIDAL login and CAPTCHA in the browser.")
    try:
        future.result()
    except Exception:
        # Expired or failed; retry once
        print("Device code expired or login failed; retrying login flow...")
        login, future = session.login_oauth()
        webbrowser.open(login.verification_uri_complete)
        future.result()
    if not session.check_login():
        raise RuntimeError("TIDAL login ultimately failed")
    print("TIDAL login successful.")
    return session

# -------- Tidal Search --------
def find_tidal_track(session, title, artist):
    query = f"{title} {artist}"
    result = session.search(query, models=[tidalapi.Track])
    tracks = result.get('tracks', [])
    if tracks:
        return f"https://tidal.com/browse/track/{tracks[0].id}"
    return None

# -------- DoubleDouble Download --------
def download_with_doubledouble(url):
    driver.get("https://doubledouble.top")
    inp = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "dl-input"))
    )
    inp.clear()
    inp.send_keys(url)
    driver.find_element(By.ID, "dl-button").click()
    time.sleep(RATE_LIMIT)

# -------- Main Workflow --------
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
            print(f" Found: {tidal_url}")
            download_with_doubledouble(tidal_url)
            print(f" Download initiated; sleeping {RATE_LIMIT}s...")
        else:
            print(" Not found on Tidal.")
            not_found.append(f"{title} – {artist}")
    # Log missing tracks
    with open("not_found_tracks.txt", "w", encoding="utf-8") as f:
        for e in not_found:
            f.write(e + "\n")
    print("Done! See not_found_tracks.txt")

if __name__ == "__main__":
    try:
        main()
    finally:
        # Cleanup: close browser session
        driver.quit()
        # Note: do not delete chrome_user_data to preserve browser session data
