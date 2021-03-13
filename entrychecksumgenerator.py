# -*- coding: utf-8 -*-
"""
    screensaver.atv4
    Copyright (C) 2017 enen92

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


    Note: This is a standalone script to update the offline video entries and
    their checksums
"""
import hashlib
import json
import os
import sys
import urllib.request
import tarfile

apple_local_feed = os.path.join("resources", "entries.json")
tmp_folder = "tmpvideos"
apple_resources_tar = "https://sylvan.apple.com/Aerials/resources.tar"
local_tar = "resources.tar"


# Fetch the TAR file containing the latest entries.json and overwrite the local copy
def get_latest_entries_from_apple():
    print("Downloading the Apple Aerials resources.tar to disk")
    urllib.request.urlretrieve(apple_resources_tar, local_tar)
    # https://www.tutorialspoint.com/How-are-files-extracted-from-a-tar-file-using-Python
    apple_tar = tarfile.open(local_tar)
    print("Extracting entries.json from resources.tar and placing in ./resources")
    apple_tar.extract("entries.json", "resources")
    apple_tar.close()
    os.remove(local_tar)


def generate_entries_and_checksums():
    with open(apple_local_feed) as f:

        print("Starting checksum generator...")
        # Create the local directory we'll temporarily store videos for checksumming
        if not os.path.exists(tmp_folder):
            os.mkdir(tmp_folder)
        # Dictionary to store the filenames and checksum for each
        checksums = {}
        # Dictionary to store the quality levels and the size in megabytes for each
        # Within each scene, there may be: H264/HEVC, 1080p/4K, SDR/HDR
        quality_total_size_megabytes = {"url-1080-H264": 0,
                                        "url-1080-SDR": 0,
                                        "url-1080-HDR": 0,
                                        "url-4K-SDR": 0,
                                        "url-4K-HDR": 0}

        # Define the locations as a set so we get deduping
        locations = set()

        top_level = json.load(f)
        # Top-level JSON has assets array, initialAssetCount, version. Inspect each block in assets
        for block in top_level["assets"]:
            # Each block contains a location/scene whose name is stored in accessibilityLabel. These may recur
            current_scene = block["accessibilityLabel"]
            print("Processing videos for scene:", current_scene)
            locations.add(current_scene)

            # https://realpython.com/iterate-through-dictionary-python/#iterating-through-keys
            for video_version in quality_total_size_megabytes.keys():
                try:
                    # Try to look up the URL, but catch the KeyError and continue if it wasn't available
                    asset_url = block[video_version]
                    print("Downloading video:", asset_url)

                    # Construct the name and path of the local file
                    local_file_name = asset_url.split('/')[-1]
                    local_file_path = os.path.join(tmp_folder, local_file_name)
                    # Download the file to local storage
                    urllib.request.urlretrieve(asset_url, local_file_path)

                    # Get the size of the file in bytes and add it to an overall size counter
                    quality_total_size_megabytes[video_version] += os.path.getsize(local_file_path) / 1000 / 1000

                    # Try to open the file
                    with open(local_file_path, "rb") as f:
                        # Compute the checksum
                        checksum = hashlib.md5(f.read()).hexdigest()
                        # Add the checksum to the dict of checksums we're keeping
                        checksums[local_file_name] = checksum
                        # Delete the local copy of the file
                        os.remove(local_file_path)
                        print("File processed. Checksum:", checksum)
                except KeyError:
                    print("Can't find URL for asset type:", video_version)

            # Now that we've processed all videos, delete the temp directory
            os.rmdir(tmp_folder)

            # Then write the checksums to file
            with open(os.path.join("resources", "checksums.json"), "w") as f:
                print("Writing checksums to disk")
                f.write(json.dumps(checksums))

            print("Total Megabytes of all video files, per quality:")
            print(quality_total_size_megabytes)
            print("Locations seen:")
            print(locations)
            print("Stopping checksum generator...")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == "1":
            generate_entries_and_checksums()
        elif sys.argv[1] == "2":
            get_latest_entries_from_apple()
    else:
        print("Please specify option:\n "
              "1) Update checksums based on existing entries.json \n "
              "2) Update entries.json from Apple")
