#!/usr/bin/env python3
"""Sort screenshots from Desktop into date-organized folders."""

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Import logging utilities
# Try multiple import paths to handle different execution contexts
# try:
from src.utils import log_automation, get_logger
# except ImportError:
#     # Fallback: add project root to path
#     project_root = Path(__file__).parent.parent.parent
#     if str(project_root) not in sys.path:
#         sys.path.insert(0, str(project_root))
#     from src.utils import log_automation, get_logger

logger = get_logger()


def is_screenshot_file(file_path: Path) -> bool:
    """Check if a file is likely a screenshot."""
    # Common screenshot file extensions
    screenshot_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif"}
    
    if file_path.suffix.lower() not in screenshot_extensions:
        return False
    
    # Check for common screenshot naming patterns
    name_lower = file_path.stem.lower()
    screenshot_patterns = [
        r"^screenshot",
        r"^screen shot",
        r"^screen capture",
        r"^capture",
        r"^img_\d+",  # Some systems use img_12345 format
    ]
    
    return any(re.match(pattern, name_lower) for pattern in screenshot_patterns)


def get_file_date(file_path: Path) -> datetime:
    """Get the creation date for a file."""
    stat = file_path.stat()
    # Use creation time (birthtime) on macOS, fall back to modification time if not available
    try:
        creation_time = stat.st_birthtime
    except AttributeError:
        # Fall back to modification time on systems without birthtime
        creation_time = stat.st_mtime
    return datetime.fromtimestamp(creation_time)


@log_automation
def main():
    """Main function to sort screenshots."""
    # Get Desktop and Screenshots paths
    home = Path.home()
    desktop = home / "Desktop"
    screenshots_base = home / "Screenshots"
    
    if not desktop.exists():
        logger.error(f"Desktop folder not found at {desktop}")
        return 1
    
    # Create Screenshots base folder if it doesn't exist
    screenshots_base.mkdir(exist_ok=True)
    logger.debug(f"Using screenshots directory: {screenshots_base}")
    
    # Find all screenshot files on Desktop
    screenshot_files = [
        f for f in desktop.iterdir()
        if f.is_file() and is_screenshot_file(f)
    ]
    
    if not screenshot_files:
        logger.info("No screenshots found on Desktop.")
        return 0
    
    logger.info(f"Found {len(screenshot_files)} screenshot(s) to organize...")
    
    moved_count = 0
    error_count = 0
    
    for screenshot in screenshot_files:
        try:
            # Get the date for this screenshot
            file_date = get_file_date(screenshot)
            date_folder = file_date.strftime("%Y-%m-%d")
            
            # Create date folder in Screenshots directory
            target_folder = screenshots_base / date_folder
            target_folder.mkdir(exist_ok=True)
            
            # Determine target path (handle duplicates)
            target_path = target_folder / screenshot.name
            counter = 1
            while target_path.exists():
                stem = screenshot.stem
                suffix = screenshot.suffix
                target_path = target_folder / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # Move the file
            shutil.move(str(screenshot), str(target_path))
            logger.info(f"Moved: {screenshot.name} -> {target_path}")
            moved_count += 1
            
        except Exception as e:
            logger.error(f"Error moving {screenshot.name}: {e}")
            error_count += 1
    
    logger.info(f"Completed: {moved_count} moved, {error_count} errors")
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

