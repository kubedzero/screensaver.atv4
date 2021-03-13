# -*- coding: utf-8 -*-
"""
    screensaver.atv4
    Copyright (C) 2015-2017 enen92

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
"""
import json
import xbmc
import os
import xbmcvfs
import ssl
import tarfile
from random import shuffle
from .commonatv import apple_resources_tar, applelocalfeed, addon, PY3

if PY3:
    import urllib.request
else:
    from urllib2 import Request, urlopen


class AtvPlaylist:
    def __init__(self, ):
        if not xbmc.getCondVisibility("Player.HasMedia"):
            # If we're not forcing offline state, update the local JSON with the copy from Apple
            if addon.getSetting("refuse-stream") == "false":

                try:
                    self.get_latest_entries_from_apple()
                    self.local_feed()
                except Exception:
                    self.local_feed()
            else:
                self.local_feed()
        else:
            self.top_level_json = {}

    # Fetch the TAR file containing the latest entries.json and overwrite the local copy
    def get_latest_entries_from_apple():
        local_tar = "resources.tar"
        print("Downloading the Apple Aerials resources.tar to disk")

        # Setup for disabling SSL cert verification, as the Apple cert is bad
        # https://stackoverflow.com/questions/43204012/how-to-disable-ssl-verification-for-urlretrieve
        ssl._create_default_https_context = ssl._create_unverified_context

        urllib.request.urlretrieve(apple_resources_tar, local_tar)
        # https://www.tutorialspoint.com/How-are-files-extracted-from-a-tar-file-using-Python
        apple_tar = tarfile.open(local_tar)
        print("Extracting entries.json from resources.tar and placing in ./resources")
        apple_tar.extract("entries.json", "resources")
        apple_tar.close()
        os.remove(local_tar)

    # Create a class variable with the JSON loaded and parseable
    def local_feed(self):
        with open(applelocalfeed, "r") as f:
            self.top_level_json = json.loads(f.read())

    def getPlaylistJson(self):
        return self.top_level_json

    def getPlaylist(self):

        self.playlist = []
        if self.top_level_json:
            # Top-level JSON has assets array, initialAssetCount, version. Inspect each block in assets
            for block in self.top_level_json["assets"]:
                # Each block contains a location/scene whose name is stored in accessibilityLabel. These may recur
                # TODO grab only 4K SDR for now, but later fall back to others
                url = block['url-4K-SDR']
                file_name = url.split("/")[-1]
                location = block['accessibilityLabel']

                # By default, we assume a local copy of the file doesn't exist
                exists_on_disk = False

                # Inspect the disk to see if the file exists in the download location
                local_file_path = os.path.join(addon.getSetting("download-folder"), file_name)
                if xbmcvfs.exists(local_file_path):
                    # Overwrite the Apple URL with the path to the file on disk
                    url = local_file_path
                    # Mark that the file exists on disk
                    exists_on_disk = True

                # If the file exists locally or we're not in offline mode, add it to the playlist
                if exists_on_disk or addon.getSetting("refuse-stream") == "false":
                    self.playlist.append(url)
                    # # build setting
                    # thisvideosetting = "enable-" + location.lower().replace(" ", "")
                    # if addon.getSetting(thisvideosetting) == "true":
                    #     self.playlist.append(url)

            # Now that we're done building the playlist, shuffle and return to the caller
            shuffle(self.playlist)
            xbmc.log(str(self.playlist), xbmc.LOGDEBUG)
            return self.playlist
        else:
            return None
