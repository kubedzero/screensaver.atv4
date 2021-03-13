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
import xbmcvfs
from .commonatv import dialog, addon, translate, places
from .playlist import AtvPlaylist
from .downloader import Downloader

# Parse the JSON to get a list of URLs and download the files to the download folder
def offline():
    if addon.getSetting("download-folder") != "" and xbmcvfs.exists(addon.getSetting("download-folder")):
        choose = dialog.select(translate(32014),places)
        if choose > -1:
            # Initialize the Playlist class, which will (down)load the JSON containing URLs
            atv_playlist = AtvPlaylist()
            top_level_json = atv_playlist.getPlaylistJson()
            download_list = []
            if top_level_json:
                # Top-level JSON has assets array, initialAssetCount, version. Inspect each block in assets
                for block in top_level_json["assets"]:
                    # Each block contains a location/scene whose name is stored in accessibilityLabel. These may recur
                    # TODO grab only 4K SDR for now, but later fall back to others
                    download_list.append(block['url-4K-SDR'])

            # call downloader
            if download_list:
                down = Downloader()
                down.downloadall(download_list)
            else:
                dialog.ok(translate(32000), translate(32012))
    else:
        dialog.ok(translate(32000), translate(32013))


