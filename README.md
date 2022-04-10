# itch.io Downloader

itch.io Downloader is a python script that allows you to download all games bound to your itch.io account. It was
originally based https://github.com/K3VRAL/Itch.io-Bundle-Downloader but there is no code from it left.

Note that you can only download games from itch.io with this which are bound to your account. You cannot pirate games on
itch.io with that.

## Requirements

- enough storage for your games.
- itch.io login cookies in a Netscape cookies.txt format (see below)
- an operating system which is supported by Python 3.

## Usage

- login to itch.io with your web browser.
- export your cookies to a cookies.txt file. You only need the cookies for itch.io, you can delete the rest (with a text
  editor).
- copy the cookie file in the same directory and rename it to 'cookies-itch.txt'
- edit the itch-downloader.ini to set up your download directory.
- run the script with python itch-downloader.py or python3 itch-downloader.py

## Tips and Tricks

- downloaded files are checked with the online version. if they are identical, they will be skipped.
- for binding your games to your account (itch.io does not do that automatically with bundles) you should install an
  user script extension (like Tampermonkey) and a user scripts which can bind games automatically to your account,
  like "itch.io bundle to library" ( https://greasyfork.org/en/scripts/427686-itch-io-bundle-to-library )
- for exporting cookies, there is the addon "cookies.txt"
  for [Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
  or [Chrome](https://chrome.google.com/webstore/detail/cookiestxt/njabckikapfpffapmjgojcnbfjonfjfg?hl=en)

## Known bugs and caveats

These known limitations may be fixed in the future, pull requests for extending the functionality and fixing bugs are
welcome.

- once the script runs, you can only stop it with control+c
- there may be games which cannot be downloaded, because the developers put them on a dropbox or google drive, though
  this will be written to stdout as a stern notice that the script is unable to download it.
- currently, there is no filtering by operating system. everything is downloaded.
- currently, there is no blacklist for not downloading stuff.
- currently, non-games (PDFs, art assets or similar things are not downloaded)


