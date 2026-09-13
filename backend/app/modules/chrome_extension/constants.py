"""Constants for the Chrome Extension module."""

import os

CHROME_EXTENSION_ID = os.environ.get("CHROME_EXTENSION_ID", "")

CHROME_WEBSTORE_URL = (
    f"https://chromewebstore.google.com/detail/selfpublisherforge/{CHROME_EXTENSION_ID}" if CHROME_EXTENSION_ID else ""
)

# Current extension version info served by the /version endpoint.
# Bump these values when publishing a new extension release.
EXTENSION_VERSION = "1.0.0"
EXTENSION_MIN_VERSION = "1.0.0"
EXTENSION_UPDATE_URL = CHROME_WEBSTORE_URL
EXTENSION_CHANGELOG = "Initial release"
