#!/usr/bin/env python
"""
Script to process songs using Y2Mate website automation.
This script loads the Y2Mate website and processes multiple
song URLs for MP3 conversion.
"""

# pylint: disable=broad-exception-caught

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import TypedDict

import requests
import yaml
from mutagen import File
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Song(TypedDict, total=False):
    """Song dictionary with url, id, and albumArtUrl."""

    url: str
    id: str
    albumArtUrl: str


def setup_driver(songs_dir):
    """Set up Chrome WebDriver with appropriate options and download preferences."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Set download preferences
    preferences = {
        "download.default_directory": str(songs_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.automatic_downloads": 1,
    }
    chrome_options.add_experimental_option("prefs", preferences)

    try:
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome WebDriver initialized successfully")
        return driver
    except WebDriverException as e:
        logger.error("Failed to initialize Chrome WebDriver: %s", e)
        logger.info("Make sure ChromeDriver is installed and in your PATH")
        raise


def load_songs_from_yaml(yaml_file_path):
    """
    Load songs from the lit_up_config.yaml file.

    Args:
        yaml_file_path: Path to the lit_up_config.yaml file

    Returns:
        list: List of song dictionaries with 'url' and 'id' keys
    """
    try:
        with open(yaml_file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if "songs" not in data:
            logger.error("No 'songs' key found in YAML file")
            return []

        songs = data["songs"]
        if not isinstance(songs, list):
            logger.error("'songs' should be a list")
            return []

        # Validate each song has required fields
        valid_songs = []
        for i, song in enumerate(songs):
            if not isinstance(song, dict):
                logger.warning("Song %s is not a dictionary, skipping", i + 1)
                continue

            if "url" not in song or "id" not in song:
                logger.warning(
                    "Song %s missing 'url' or 'id' field, skipping",
                    i + 1,
                )
                continue

            valid_songs.append(song)

        logger.info(
            "Loaded %s songs from %s",
            len(valid_songs),
            yaml_file_path,
        )
        return valid_songs

    except FileNotFoundError:
        logger.error("YAML file not found: %s", yaml_file_path)
        return []
    except yaml.YAMLError as e:
        logger.error("Error parsing YAML file: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected error loading YAML file: %s", e)
        return []


def create_filename_from_id(song_id, extension="mp3"):
    """
    Create a filename from a song ID.

    Args:
        song_id: The song ID from the YAML file
        extension: File extension (default: "mp3")

    Returns:
        str: Safe filename using the song ID
    """
    # Clean the ID to make it filesystem-safe
    safe_id = str(song_id).replace("/", "_").replace("\\", "_").replace(":", "_")
    return f"{safe_id}.{extension}"


def get_mp3_duration(mp3_file_path):
    """
    Get the duration of an MP3 file in seconds.

    Args:
        mp3_file_path: Path to the MP3 file

    Returns:
        float: Duration in seconds, or None if unable to determine
    """
    try:
        audio_file = File(mp3_file_path)
        if audio_file is not None and hasattr(audio_file, "info"):
            duration = audio_file.info.length
            logger.info(
                "✓ MP3 duration: %.2f seconds (%s)",
                duration,
                format_duration(duration),
            )
            return duration

        logger.warning("⚠ Could not read MP3 file: %s", mp3_file_path)
        return None
    except Exception as e:
        logger.warning("⚠ Error getting MP3 duration: %s", e)
        return None


def format_duration(seconds):
    """
    Format duration in seconds to MM:SS format.

    Args:
        seconds: Duration in seconds

    Returns:
        str: Formatted duration string (MM:SS)
    """
    if seconds is None:
        return "0:00"

    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"


def download_album_art(album_art_url, output_path):
    """
    Download album art from URL and save to specified path.

    Args:
        album_art_url: URL of the album art image
        output_path: Path where to save the image

    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        logger.info("Downloading album art from: %s", album_art_url)

        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Download the image
        response = requests.get(album_art_url, timeout=30)
        response.raise_for_status()

        # Save the image
        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info("✓ Album art downloaded: %s", output_path.name)
        return True

    except Exception as e:
        logger.error("✗ Failed to download album art: %s", e)
        return False


def check_chrome_downloads(driver):
    """
    Check Chrome's download status using JavaScript.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        list: List of download information
    """
    try:
        # Execute JavaScript to get download status
        downloads = driver.execute_script(
            """
            return new Promise((resolve) => {
                chrome.downloads.search({}, (downloads) => {
                    resolve(downloads || []);
                });
            });
        """
        )
        return downloads
    except Exception as e:
        logger.warning("Could not check Chrome downloads: %s", e)
        return []


def _find_song_input(driver: WebDriver) -> WebElement | None:
    """Find the song URL input element."""
    try:
        input_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "v"))
        )
        logger.info("✓ Found input element with id 'v'")
        return input_element
    except TimeoutException:
        logger.error("✗ Input element with id 'v' not found")
        return None


def _verify_mp3_button(driver: WebDriver) -> bool:
    """Verify the MP3 button exists; warn if it doesn't show MP3 text."""
    try:
        mp3_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "f"))
        )
        button_text = mp3_button.text.strip()
        if "MP3" in button_text.upper():
            logger.info("✓ MP3 button found with text: '%s'", button_text)
        else:
            logger.warning("⚠ MP3 button found but text is: '%s'", button_text)
        return True
    except TimeoutException:
        logger.error("✗ Button with id 'f' not found")
        return False


def _wait_for_conversion(driver: WebDriver) -> bool:
    """Wait for conversion progress to start and then complete."""
    try:
        logger.info("Waiting for progress div to appear...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "progress"))
        )
        logger.info("✓ Progress div found with id 'progress'")
    except TimeoutException:
        logger.warning("⚠ Progress div with id 'progress' not found within timeout")
        return False

    try:
        logger.info("Waiting for conversion to complete (progress id removal)...")
        WebDriverWait(driver, 300).until(  # 5 minute timeout for conversion
            lambda d: not d.find_elements(By.ID, "progress")
        )
        logger.info("✓ Conversion completed - progress id removed")
        return True
    except TimeoutException:
        logger.warning(
            "⚠ Conversion timeout - progress id still present after 5 minutes"
        )
        return False


def _click_download_button(driver: WebDriver) -> bool:
    """Find and click the download button after conversion."""
    logger.info("Looking for download button...")
    try:
        form_element = driver.find_element(By.TAG_NAME, "form")
        form_divs = form_element.find_elements(By.TAG_NAME, "div")
        if len(form_divs) < 2:
            logger.error("✗ Could not find the second div in form")
            return False

        progress_div = form_divs[1]  # Second div (index 1)
        download_button = progress_div.find_element(By.TAG_NAME, "button")
        logger.info("✓ Found download button")

        download_button.click()
        logger.info("✓ Clicked download button")
        return True
    except Exception as e:
        logger.error("✗ Error during download process: %s", e)
        return False


def _wait_for_download(
    songs_dir: Path, song_id: str, download_timeout: int = 120
) -> bool:
    """Wait for the MP3 to appear; rename if needed and log debugging info."""
    expected_filename = create_filename_from_id(song_id, "mp3")
    expected_filepath = songs_dir / expected_filename

    logger.info("Waiting for download to complete: %s", expected_filename)
    logger.info("Expected file path: %s", expected_filepath)

    start_time = time.time()
    while time.time() - start_time < download_timeout:
        if expected_filepath.exists():
            logger.info("✓ Download completed: %s", expected_filename)
            get_mp3_duration(expected_filepath)
            return True

        mp3_files = list(songs_dir.glob("*.mp3"))
        if mp3_files:
            recent_files = [
                f for f in mp3_files if time.time() - f.stat().st_mtime < 30
            ]
            if recent_files:
                downloaded_file = recent_files[0]
                logger.info("✓ Found recent MP3 file: %s", downloaded_file.name)
                try:
                    downloaded_file.rename(expected_filepath)
                    logger.info(
                        "✓ Renamed %s to %s",
                        downloaded_file.name,
                        expected_filename,
                    )
                    return True
                except Exception as e:
                    logger.warning("⚠ Could not rename file: %s", e)
                    return True  # Still successful since we found the file

        # Debugging: periodically list files in download directory
        if int(time.time() - start_time) % 10 == 0:  # Every 10 seconds
            existing_files = list(songs_dir.glob("*"))
            if existing_files:
                logger.info(
                    "Files in download directory: %s",
                    [f.name for f in existing_files],
                )
            else:
                logger.info("No files found in download directory yet")

        time.sleep(1)

    existing_files = list(songs_dir.glob("*"))
    logger.warning(
        "Download timeout. Files in directory: %s",
        [f.name for f in existing_files],
    )
    logger.warning("⚠ Download timeout - file not found: %s", expected_filename)
    return False


def process_single_song(driver: WebDriver, song: Song, songs_dir: Path) -> bool:
    """
    Process a single song through Y2Mate conversion and download.

    Args:
        driver: Selenium WebDriver instance
        song: Dictionary containing 'url', 'id', and 'albumArtUrl' keys
        songs_dir: Directory to save the downloaded MP3 file

    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        song_url = song["url"]
        song_id = song["id"]
        logger.info("Processing song: %s", song_url)

        input_element = _find_song_input(driver)
        if input_element is None:
            return False

        input_element.clear()
        input_element.send_keys(song_url)
        logger.info("✓ Entered song URL: %s", song_url)

        if not _verify_mp3_button(driver):
            return False

        input_element.send_keys(Keys.RETURN)
        logger.info("✓ Pressed Enter key in input field")

        if not _wait_for_conversion(driver):
            return False

        if not _click_download_button(driver):
            return False

        time.sleep(2)  # Wait a moment for the download to start
        return _wait_for_download(songs_dir, song_id)

    except Exception as e:
        logger.error("Error processing song %s: %s", song_url, e)
        return False


def process_songs_on_y2mate(
    driver, songs, songs_dir, album_art_dir, base_url="https://y2mate.nu/R2lu/"
):
    """
    Load the Y2Mate website and process multiple songs.

    Args:
        driver: Selenium WebDriver instance
        songs: List of song dictionaries with 'url', 'id', and 'albumArtUrl' keys
        songs_dir: Directory to save downloaded MP3 files
        album_art_dir: Directory to save downloaded album art
        base_url: Y2Mate website URL

    Returns:
        dict: Results of processing each song
    """
    results = {}

    try:
        logger.info("Loading Y2Mate website: %s", base_url)
        driver.get(base_url)

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logger.info("✓ Page loaded successfully")

        # Check for div with id "logo" to verify we're on the right page
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "logo"))
            )
            logger.info("✓ Div with id 'logo' found - confirmed on Y2Mate website")
        except TimeoutException:
            logger.warning("⚠ Div with id 'logo' not found - proceeding anyway")

        # Process each song
        for i, song in enumerate(songs, 1):
            logger.info("Processing song %s/%s", i, len(songs))

            mp3_filename = create_filename_from_id(song["id"], "mp3")
            mp3_filepath = songs_dir / mp3_filename

            album_art_filename = create_filename_from_id(song["id"], "jpg")
            album_art_filepath = album_art_dir / album_art_filename

            album_art_exists = (
                album_art_filepath.exists()
                if ("albumArtUrl" in song and song["albumArtUrl"])
                else True
            )

            # If both files exist, skip processing entirely
            if mp3_filepath.exists() and album_art_exists:
                logger.info(
                    "✓ Both MP3 and album art already exist for song %s - skipping",
                    song["id"],
                )
                logger.info("  MP3: %s", mp3_filename)
                if "albumArtUrl" in song and song["albumArtUrl"]:
                    logger.info("  Album Art: %s", album_art_filename)
                results[song["url"]] = True
                continue

            # Download album art if it doesn't exist (but MP3 might exist)
            if "albumArtUrl" in song and song["albumArtUrl"]:
                if not album_art_filepath.exists():
                    logger.info(
                        "Album art missing, downloading: %s",
                        album_art_filename,
                    )
                    download_album_art(song["albumArtUrl"], album_art_filepath)
                else:
                    logger.info("✓ Album art already exists: %s", album_art_filename)

            # Check if MP3 file exists - if it does, skip song processing
            if mp3_filepath.exists():
                logger.info(
                    "✓ MP3 file already exists: %s - skipping download",
                    mp3_filename,
                )
                results[song["url"]] = True
                continue

            # MP3 doesn't exist, process the song
            logger.info("MP3 file not found, processing song: %s", mp3_filename)
            processed_song_success = process_single_song(driver, song, songs_dir)
            results[song["url"]] = processed_song_success

            # Wait between songs to avoid overwhelming the server
            if i < len(songs):
                logger.info("Waiting 3 seconds before next song...")
                time.sleep(3)

                # Reload the page to reset the form state for the next song
                logger.info("Reloading page to reset form state...")
                driver.refresh()

                # Wait for page to reload
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                logger.info("✓ Page reloaded successfully")

        return results

    except TimeoutException:
        logger.error("Page failed to load within timeout period")
        return results
    except WebDriverException as e:
        logger.error("WebDriver error occurred: %s", e)
        return results


def main():
    """Main function to run the song processing automation."""
    # pylint: disable=too-many-locals
    parser = argparse.ArgumentParser(
        description="Process songs using Y2Mate website automation"
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to lit_up_config.yaml",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("."),
        help="Output directory (default: current directory)",
    )

    args = parser.parse_args()

    driver = None

    try:
        logger.info("Starting Y2Mate song processing automation...")

        # Set up directories
        out_dir = args.out_dir.resolve()
        songs_dir = out_dir / "songs"
        album_art_dir = out_dir / "album_art"

        songs_dir.mkdir(parents=True, exist_ok=True)
        album_art_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Songs directory: %s", songs_dir)
        logger.info("Album art directory: %s", album_art_dir)

        # Load songs from YAML file
        yaml_file_path = args.config.resolve()
        songs = load_songs_from_yaml(yaml_file_path)
        if not songs:
            logger.error("No songs found in lit_up_config.yaml file")
            logger.info(
                "Please ensure lit_up_config.yaml exists with the correct format"
            )
            logger.info("Example format:")
            logger.info("songs:")
            logger.info("  - url: 'https://youtube.com/watch?v=abc123'")
            logger.info("    id: 'unique-song-id'")
            logger.info("    albumArtUrl: 'https://example.com/album-art.jpg'")
            return False

        # Set up WebDriver with download preferences
        driver = setup_driver(songs_dir)

        # Process songs on Y2Mate
        results = process_songs_on_y2mate(driver, songs, songs_dir, album_art_dir)

        # Report results
        successful = sum(1 for success in results.values() if success)
        total = len(results)

        logger.info(
            "Processing complete: %s/%s songs processed successfully", successful, total
        )

        for song_url, processed_song_success in results.items():
            status = "✓ SUCCESS" if processed_song_success else "✗ FAILED"
            # Find the corresponding song to get the ID
            song = next((s for s in songs if s["url"] == song_url), None)
            if song:
                mp3_filename = create_filename_from_id(song["id"], "mp3")
                album_art_filename = create_filename_from_id(song["id"], "jpg")
                logger.info("  %s: %s", status, song_url)
                logger.info("    MP3: %s", mp3_filename)
                logger.info("    Album Art: %s", album_art_filename)
            else:
                logger.info("  %s: %s", status, song_url)

        return successful == total

    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
        return False

    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
