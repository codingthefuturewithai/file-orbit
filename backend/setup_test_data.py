#!/usr/bin/env python3
"""
Set up test directories and files for testing file transfers.
This creates local directories that can be used as endpoints.
"""
import os
import sys
from pathlib import Path

# Test directories
TEST_DIRS = [
    "/tmp/pbs-rclone-test/source",
    "/tmp/pbs-rclone-test/dest",
    "/tmp/pbs-rclone-test/archive",
    "/tmp/pbs-rclone-test/5tb-limited"
]

# Test files to create
TEST_FILES = [
    "test-video-1.mp4",
    "test-video-2.mp4",
    "test-video-3.mov",
    "document.pdf",
    "image.jpg"
]

def setup_test_data():
    """Create test directories and files"""
    print("Setting up test data...")
    
    # Create directories
    for dir_path in TEST_DIRS:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create test files in source directory
    source_dir = Path(TEST_DIRS[0])
    for filename in TEST_FILES:
        file_path = source_dir / filename
        # Create files with some content
        size_mb = 10 if filename.endswith(('.mp4', '.mov')) else 1
        with open(file_path, 'wb') as f:
            # Write random data (size in MB)
            f.write(os.urandom(size_mb * 1024 * 1024))
        print(f"Created file: {file_path} ({size_mb}MB)")
    
    # Create subdirectory with more files
    subdir = source_dir / "videos" / "2024"
    subdir.mkdir(parents=True, exist_ok=True)
    for i in range(1, 4):
        file_path = subdir / f"episode-{i}.mp4"
        with open(file_path, 'wb') as f:
            f.write(os.urandom(5 * 1024 * 1024))
        print(f"Created file: {file_path} (5MB)")
    
    print("\nTest data setup complete!")
    print(f"\nSource directory: {TEST_DIRS[0]}")
    print(f"Files created: {len(TEST_FILES) + 3}")
    print("\nYou can now update the endpoints in the database to use these paths.")

def cleanup_test_data():
    """Remove test directories"""
    import shutil
    
    print("Cleaning up test data...")
    base_dir = "/tmp/pbs-rclone-test"
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
        print(f"Removed {base_dir}")
    else:
        print("Test data directory not found")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_test_data()
    else:
        setup_test_data()