# Changelog for itch.io Downloader

## 0.5.3 (2022-04-16)

- download now adds datestamp to archives
- renames already downloaded files appropriately
- added webpage screenshot of gamepage (user has to provide service url)
- added screenshot download option
- added operating system selection (not yet active)
- still hardcoded that only windows and android will be downloaded

## 0.5.2 (2022-04-12)

- added a primitive download continue (tracks download position and resumes download at number)
- fixed (hopefully) "SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC"
- fixed missing content-disposition
- some reformatting

## 0.5.1 (2022-04-10)

- fixed config file reading
- some adjustments for win32 platform

## 0.5 (2022-04-10)
- 

- first numbered revision
- configuration put into proper .ini file
- rewritten README.md
- Changelog.md
- displays xxx / number of games during downloading games
- proper requirements.txt

## unnamed revisions (2022-04-10)

- basic working revisions, ironed out bugs and such
- configuration baked into script
- total rewrite of bundle downloader