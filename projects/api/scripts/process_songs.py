#!/usr/bin/env python
"""
Script to process songs using Y2Mate website automation.
This script loads the Y2Mate website and processes multiple song URLs for MP3 conversion.
"""

import argparse
import os
import time
import logging
import urllib.parse
import yaml
import requests
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from mutagen import File

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_driver(songs_dir):
    """Set up Chrome WebDriver with appropriate options and download preferences."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Set download preferences
    prefs = {
        "download.default_directory": str(songs_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.automatic_downloads": 1,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    try:
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome WebDriver initialized successfully")
        return driver
    except WebDriverException as e:
        logger.error(f"Failed to initialize Chrome WebDriver: {e}")
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
        with open(yaml_file_path, "r") as file:
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
                logger.warning(f"Song {i+1} is not a dictionary, skipping")
                continue

            if "url" not in song or "id" not in song:
                logger.warning(f"Song {i+1} missing 'url' or 'id' field, skipping")
                continue

            valid_songs.append(song)

        logger.info(f"Loaded {len(valid_songs)} songs from {yaml_file_path}")
        return valid_songs

    except FileNotFoundError:
        logger.error(f"YAML file not found: {yaml_file_path}")
        return []
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading YAML file: {e}")
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
                f"✓ MP3 duration: {duration:.2f} seconds ({format_duration(duration)})"
            )
            return duration
        else:
            logger.warning(f"⚠ Could not read MP3 file: {mp3_file_path}")
            return None
    except Exception as e:
        logger.warning(f"⚠ Error getting MP3 duration: {e}")
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
        logger.info(f"Downloading album art from: {album_art_url}")

        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Download the image
        response = requests.get(album_art_url, timeout=30)
        response.raise_for_status()

        # Save the image
        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info(f"✓ Album art downloaded: {output_path.name}")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to download album art: {e}")
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
        logger.warning(f"Could not check Chrome downloads: {e}")
        return []


def process_single_song(driver, song, songs_dir):
    """
    Process a single song through Y2Mate conversion and download.

    Args:
        driver: Selenium WebDriver instance
        song: Dictionary containing 'url', 'id', and 'albumArtUrl' keys
        songs_dir: Directory to save the downloaded MP3 file

    Returns:
        bool: True if processing was successful, False otherwise
    """
    song_url = song["url"]
    song_id = song["id"]
    try:
        logger.info(f"Processing song: {song_url}")

        # Find the input element with id "v"
        try:
            input_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "v"))
            )
            logger.info("✓ Found input element with id 'v'")
        except TimeoutException:
            logger.error("✗ Input element with id 'v' not found")
            return False

        # Clear the input field and enter the song URL
        input_element.clear()
        input_element.send_keys(song_url)
        logger.info(f"✓ Entered song URL: {song_url}")

        # Verify the button with id "f" has "MP3" text
        try:
            mp3_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "f"))
            )
            button_text = mp3_button.text.strip()
            if "MP3" in button_text.upper():
                logger.info(f"✓ MP3 button found with text: '{button_text}'")
            else:
                logger.warning(f"⚠ MP3 button found but text is: '{button_text}'")
        except TimeoutException:
            logger.error("✗ Button with id 'f' not found")
            return False

        # Press Enter key in the input field
        input_element.send_keys(Keys.RETURN)
        logger.info("✓ Pressed Enter key in input field")

        # Wait for the second div in body > form to get the id "progress"
        try:
            logger.info("Waiting for progress div to appear...")
            progress_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "progress"))
            )
            logger.info("✓ Progress div found with id 'progress'")
        except TimeoutException:
            logger.warning("⚠ Progress div with id 'progress' not found within timeout")
            return False

        # Wait until the "progress" id attribute is removed
        try:
            logger.info("Waiting for conversion to complete (progress id removal)...")
            WebDriverWait(driver, 300).until(  # 5 minute timeout for conversion
                lambda driver: not driver.find_elements(By.ID, "progress")
            )
            logger.info("✓ Conversion completed - progress id removed")
        except TimeoutException:
            logger.warning(
                "⚠ Conversion timeout - progress id still present after 5 minutes"
            )
            return False

        # Find the div that previously had the "progress" id and click its first child button
        try:
            logger.info("Looking for download button...")
            # Find the form element first
            form_element = driver.find_element(By.TAG_NAME, "form")

            # Find the second div in the form (which should be the one that had the progress id)
            form_divs = form_element.find_elements(By.TAG_NAME, "div")
            if len(form_divs) >= 2:
                progress_div = form_divs[1]  # Second div (index 1)

                # Find the first child button of this div
                download_button = progress_div.find_element(By.TAG_NAME, "button")
                logger.info("✓ Found download button")

                # Click the download button
                download_button.click()
                logger.info("✓ Clicked download button")

                # Wait a moment for the download to start
                time.sleep(2)

                # Wait for download to complete
                expected_filename = create_filename_from_id(song_id, "mp3")
                expected_filepath = songs_dir / expected_filename

                logger.info(f"Waiting for download to complete: {expected_filename}")
                logger.info(f"Expected file path: {expected_filepath}")

                # Wait up to 2 minutes for the file to appear
                download_timeout = 120
                start_time = time.time()

                while time.time() - start_time < download_timeout:
                    # Check for the exact expected file
                    if expected_filepath.exists():
                        logger.info(f"✓ Download completed: {expected_filename}")
                        # Get the duration of the downloaded MP3
                        duration = get_mp3_duration(expected_filepath)
                        return True

                    # Check for any MP3 files that might have been downloaded with different names
                    mp3_files = list(songs_dir.glob("*.mp3"))
                    if mp3_files:
                        # Check if any MP3 file was created recently (within last 30 seconds)
                        recent_files = [
                            f for f in mp3_files if time.time() - f.stat().st_mtime < 30
                        ]
                        if recent_files:
                            downloaded_file = recent_files[0]
                            logger.info(
                                f"✓ Found recent MP3 file: {downloaded_file.name}"
                            )

                            # Rename the downloaded file to use the song ID
                            try:
                                downloaded_file.rename(expected_filepath)
                                logger.info(
                                    f"✓ Renamed {downloaded_file.name} to {expected_filename}"
                                )
                                # Get the duration of the renamed MP3
                                duration = get_mp3_duration(expected_filepath)
                                return True
                            except Exception as e:
                                logger.warning(f"⚠ Could not rename file: {e}")
                                # Get duration of the original file
                                duration = get_mp3_duration(downloaded_file)
                                return True  # Still consider it successful since we found the file

                    # Check for any files in the download directory (debugging)
                    if int(time.time() - start_time) % 10 == 0:  # Every 10 seconds
                        existing_files = list(songs_dir.glob("*"))
                        if existing_files:
                            logger.info(
                                f"Files in download directory: {[f.name for f in existing_files]}"
                            )
                        else:
                            logger.info("No files found in download directory yet")

                    time.sleep(1)

                # Final check - list all files in directory for debugging
                existing_files = list(songs_dir.glob("*"))
                logger.warning(
                    f"Download timeout. Files in directory: {[f.name for f in existing_files]}"
                )
                logger.warning(
                    f"⚠ Download timeout - file not found: {expected_filename}"
                )
                return False

            else:
                logger.error("✗ Could not find the second div in form")
                return False

        except Exception as e:
            logger.error(f"✗ Error during download process: {e}")
            return False

        return True

    except Exception as e:
        logger.error(f"Error processing song {song_url}: {e}")
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
        logger.info(f"Loading Y2Mate website: {base_url}")
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
            logger.info(f"Processing song {i}/{len(songs)}")

            # Check if MP3 file already exists
            mp3_filename = create_filename_from_id(song["id"], "mp3")
            mp3_filepath = songs_dir / mp3_filename

            # Check if album art already exists
            album_art_filename = create_filename_from_id(song["id"], "jpg")
            album_art_filepath = album_art_dir / album_art_filename

            # Check if both MP3 and album art already exist
            mp3_exists = mp3_filepath.exists()
            album_art_exists = (
                album_art_filepath.exists()
                if ("albumArtUrl" in song and song["albumArtUrl"])
                else True
            )

            # If both files exist, skip processing entirely
            if mp3_exists and album_art_exists:
                logger.info(
                    f"✓ Both MP3 and album art already exist for song {song['id']} - skipping"
                )
                logger.info(f"  MP3: {mp3_filename}")
                if "albumArtUrl" in song and song["albumArtUrl"]:
                    logger.info(f"  Album Art: {album_art_filename}")
                results[song["url"]] = True
                continue

            # Download album art if it doesn't exist (but MP3 might exist)
            if "albumArtUrl" in song and song["albumArtUrl"]:
                if not album_art_filepath.exists():
                    logger.info(f"Album art missing, downloading: {album_art_filename}")
                    download_album_art(song["albumArtUrl"], album_art_filepath)
                else:
                    logger.info(f"✓ Album art already exists: {album_art_filename}")

            # Check if MP3 file exists - if it does, skip song processing
            if mp3_filepath.exists():
                logger.info(
                    f"✓ MP3 file already exists: {mp3_filename} - skipping download"
                )
                results[song["url"]] = True
                continue

            # MP3 doesn't exist, process the song
            logger.info(f"MP3 file not found, processing song: {mp3_filename}")
            success = process_single_song(driver, song, songs_dir)
            results[song["url"]] = success

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
        logger.error(f"WebDriver error occurred: {e}")
        return results


def main():
    """Main function to run the song processing automation."""
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

        logger.info(f"Songs directory: {songs_dir}")
        logger.info(f"Album art directory: {album_art_dir}")

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
            f"Processing complete: {successful}/{total} songs processed successfully"
        )

        for song_url, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            # Find the corresponding song to get the ID
            song = next((s for s in songs if s["url"] == song_url), None)
            if song:
                mp3_filename = create_filename_from_id(song["id"], "mp3")
                album_art_filename = create_filename_from_id(song["id"], "jpg")
                logger.info(f"  {status}: {song_url}")
                logger.info(f"    MP3: {mp3_filename}")
                logger.info(f"    Album Art: {album_art_filename}")
            else:
                logger.info(f"  {status}: {song_url}")

        return successful == total

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False

    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed")


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
