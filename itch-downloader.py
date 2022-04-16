import configparser
import json
import os
import sys
import time
from http.cookiejar import MozillaCookieJar

import dateparser
import requests
import requests.cookies
from bs4 import BeautifulSoup

import dltool

version = "0.5.3"

def local_file_sanity_check(localfile, localsize, localdate, remotesize, remotedate):
    if not os.path.isfile(localfile):
        return False

    if localsize != remotesize:
        return False

    # date is a string, has to be converted to timestamp.
    if localdate != remotedate:
        return False

    # fall through, at this point the conditions above are satisfied
    return True

def fetch_upload(uploads_soup, dlurl, session, params, csfrtoken, gamedirectory):
    downloadid = uploads_soup.find("a")["data-upload_id"]
    dlurl_final = dlurl + "/file/" + downloadid
    dlj = session.post(dlurl_final, params=params, data=csfrtoken).json()

    if dlj["url"].split("/")[2] == "w3g3a5v6.ssl.hwcdn.net":
        # remote file check
        dlhead = session.head(dlj["url"])
        dldate = dlhead.headers["last-modified"]
        if "content-disposition" in dlhead.headers:
            dlfilename = dlhead.headers["content-disposition"].split('"')[1]
        else:
            dlfilename = dlj["url"].split("?")[0].split("/")[-1]
        dlsize = dlhead.headers["content-length"]

        # local preparation
        fulldldir = os.path.join(config["DEFAULT"]["download_directory"], gamedirectory)
        os.makedirs(fulldldir, exist_ok=True)
        fulldname = os.path.join(fulldldir, dlfilename)

        # detect mac und linux downloads
        if dlfilename.lower().endswith("mac.zip") or \
            "osx" in dlfilename.lower() or \
            "macos" in dlfilename.lower() or \
            dlfilename.lower().endswith("linux.zip") or \
            "linux" in dlfilename.lower() or \
            dlfilename.lower().endswith(".tgz") or \
            dlfilename.lower().endswith(".gz") or \
            dlfilename.lower().endswith(".deb") or \
            dlfilename.lower().endswith(".rpm") or \
            dlfilename.lower().endswith(".xz") or \
            dlfilename.lower().endswith(".bz2") or \
            dlfilename.lower().endswith(".pkg") or \
                ".app" in dlfilename.lower() or \
                dlfilename.lower().endswith(".dmg"):

            print("SKIP: {} is probably a linux or mac release.".format(dlfilename))
            if os.path.isfile(fulldname):
                os.remove(fulldname)
            time.sleep(3)
            return

        # rename files if exist.
        suf = dlfilename.split(".")[-1]
        newdlname = dlfilename.replace("." + suf, "_{}.{}".format(dateparser.parse(dldate).strftime("%Y%m%d"), suf))
        newfulldname = os.path.join(fulldldir, newdlname)

        # old format
        if os.path.isfile(fulldname):
            if os.path.exists(fulldname):
                if os.path.exists(newfulldname):
                    os.remove(newfulldname)
                os.rename(fulldname, newfulldname)
                fulldname = newfulldname

        # new filename with date stamp
        fulldname = newfulldname

        # do the download
        dltool.download_a_file(dlj["url"], filename=fulldname, session=session)
    else:
        dldomain = dlj["url"].split("/")[2]
        if dldomain == "drive.google.com":
            print("******** Download from Google Drive is UNSUPPORTED: {}.".format(dlj["url"]))
        else:
            print("")

def main(config):
    print("Download directory is '{}'.".format(config["DEFAULT"]["download_directory"]))
    time.sleep(3)

    # basic setup
    session = requests.Session()
    cookiejar = requests.cookies.RequestsCookieJar()

    cookies = MozillaCookieJar(config["DEFAULT"]["cookie_file"])
    cookies.load(ignore_expires=True, ignore_discard=True)
    cookiejar.update(cookies)

    session.cookies = cookiejar

    os.makedirs(config["DEFAULT"]["download_directory"], exist_ok=True)

    print("*** loading and parsing my claimed purchases ***")
    mypurchases_url = "https://itch.io/my-purchases"

    pagecounter = 1
    gamelist = list()
    not_a_game_list = list()
    r = session.get(mypurchases_url)
    if r.status_code == 200:
        if r.url != mypurchases_url:
            print("Not properly authenticated, please provide cookies.")
            sys.exit(1)

        # parse first page
        soup_gamepage = BeautifulSoup(r.text, "html.parser").find_all("div", class_="game_cell_data")
        for game in soup_gamepage:
            gtitle = game.find("a", class_="title game_link").text
            gurl = game.find("a", class_="button")["href"]
            platform_soup = game.find("div", class_="game_platform")
            if not platform_soup:
                # print("'{}' is not a game, skipping: {}".format(gtitle, gurl))
                not_a_game_list.append(
                    {
                        "title": gtitle,
                        "dlurl": gurl
                    }
                )
            else:
                plat = platform_soup.find("span")["class"][1]
                if plat in ["icon-windows8", "icon-android"]:
                    gamelist.append(
                        {
                            "title": gtitle,
                            "dlurl": gurl
                        }
                    )
                else:
                    print("*** unsupported platform '{}'.".format(plat))
                    sys.exit(1)

        soup_nextpage = BeautifulSoup(r.text, "html.parser").find("div", attrs={"class": "next_page forward_link"})
        while soup_nextpage:
            pagecounter = pagecounter + 1
            print(".", flush=True, end="")

            r = session.get(mypurchases_url + "?page={}".format(pagecounter))
            if r.status_code != 200:
                print(" [{}]".format(pagecounter), flush=True)
                break

            soup_gamepage = BeautifulSoup(r.text, "html.parser").find_all("div", class_="game_cell_data")
            for game in soup_gamepage:
                gtitle = game.find("a", class_="title game_link").text
                gurl = game.find("a", class_="button")["href"]
                platform_soup = game.find("div", class_="game_platform")
                if not platform_soup:
                    # print("'{}' is not a game, skipping: {}".format(gtitle, gurl))
                    not_a_game_list.append(
                        {
                            "title": gtitle,
                            "dlurl": gurl
                        }
                    )
                else:
                    gamelist.append(
                        {
                            "title": gtitle,
                            "dlurl": gurl
                        }
                    )

            soup_nextpage = BeautifulSoup(r.text, "html.parser").find("div", attrs={"class": "next_page forward_link"})

        print("")
        print("{} items found: {} downloadable games, {} non-game stuff.".format(len(gamelist) + len(not_a_game_list),
                                                                                 len(gamelist), len(not_a_game_list)))

        trackfile = os.path.join(config["DEFAULT"]["download_directory"], ".itch-downloader-track.txt")
        trackNum = 0
        if os.path.exists(trackfile):
            with open(trackfile, "r", encoding="utf-8") as f:
                trackNum = json.loads(f.read())
            f.close()
            os.remove(trackfile)

        numGames = len(gamelist)
        curGame = 0
        for g in gamelist:
            curGame = curGame + 1
            if curGame >= trackNum:
                print("")
                print(" -- [{}/{}] ".format(curGame, numGames) + g["title"])

                # trackfile
                with open(trackfile, "w", encoding="utf-8") as f:
                    json.dump(curGame, f)
                f.close()

                r = session.get(g["dlurl"])
                if r.status_code == 200:
                    # https://joemanaco.itch.io/captain-backwater/file/12961?source=game_download&key=4zsEYKAs3XzZFDUH_HS_oylA6mpOP_SyNZq5FY_S

                    dlpage_soup = BeautifulSoup(r.text, "html.parser")
                    dlpage_dlbuttons = dlpage_soup.find_all("a", class_="button download_btn")
                    dlurl = g['dlurl'].rsplit("/", 2)[0]
                    gamedirectory = g["dlurl"].split("/")[3]
                    paramPost = {"source": "game_download", "key": g["dlurl"].split("/")[5]}
                    csfrToken = dlpage_soup.find("meta", attrs={"name": "csrf_token"})["value"]
                    uploads = dlpage_soup.find("div", class_="upload_list_widget").find_all(class_="upload")
                    for u in uploads:
                        fetch_upload(u, dlurl, session, paramPost, csfrToken, gamedirectory)
                else:
                    print("Could not access download page {} !".format(g["dlurl"]))
                    sys.exit(1)

                ## fetch screenshot of game page
                if config["SCREENSHOT"]["dump_webpage"]:
                    if not config["SCREENSHOT"]["screenshot_service"].startswith("http"):
                        print("*** STOP: You have to provide a screenshot service in the configuration file.")
                        print("***       hint: include a '{}' where the target url is.")
                        if sys.platform == "win32":
                            x = input("Press ENTER to exit.")
                        sys.exit(1)

                    print("Making screenshot of {}.".format(dlurl))
                    picturedata = requests.get(config["SCREENSHOT"]["screenshot_service"].format(dlurl))
                    if picturedata.status_code != 200:
                        print("[{}] Could not retrieve picture of website!".format(picturedata.status_code))
                        sys.exit(1)
                    fulldldir = os.path.join(config["DEFAULT"]["download_directory"], gamedirectory)
                    with open(os.path.join(fulldldir, "screenshot_website.jpg"), "wb") as f:
                        f.write(picturedata.content)
                    f.close()

                ## fetch screenshot(s)
                gamepage = session.get(dlurl)
                if gamepage.status_code != 200:
                    print("*** STOP: could not load game page {}.".format(dlurl))
                    if sys.platform == "win32":
                        x = input("Press ENTER to exit.")
                    sys.exit(1)

                if config["SCREENSHOT"]["dump_screenshots"]:
                    gamepage_soup = BeautifulSoup(gamepage.text, "html.parser")
                    screenshots_soup = gamepage_soup.find_all("img", class_="screenshot")
                    if len(screenshots_soup) > 0:
                        print("Downloading {} screenshots.".format(len(screenshots_soup)))
                        c = 1
                        for ss in screenshots_soup:
                            cs = "%02d" % c
                            screenshot = session.get(ss.parent["href"])
                            if screenshot.status_code != 200:
                                print("*** STOP: could not load screenshot {}.".format(ss.parent["href"]))
                                if sys.platform == "win32":
                                    x = input("Press ENTER to exit.")
                                sys.exit(1)
                            with open(os.path.join(fulldldir, "screenshot_{}.jpg".format(cs)), "wb") as f:
                                f.write(screenshot.content)
                            f.close()
                            c = c + 1
                        print("")

                    else:
                        print("Downloading screenshots: no usable screenshot found.")
    else:
        print("Could not access {} properly [{}].".format(mypurchases_url, r.status_code))

if __name__ == "__main__":
    print("itch-downloader.py {} (c) 2022 shakeyourbunny@gmail.com".format(version))
    print("")

    config = configparser.ConfigParser()

    # initialize and load defaults
    configfile = "itch-downloader.ini"
    config['DEFAULT'] = {
        "download_directory": "Downloads",
        "cookie_file": "cookies-itch.txt"
    }
    config['OPSYS'] = {
        "windows": True,
        "linux": False,
        "macos": False,
        "android": False
    }
    config['SCREENSHOT'] = {
        "screenshot_service": "",  # you have to provide dl url for yourself
        "cmd_videodownloader": "yt-dlp",

        "dump_webpage": False,
        "dump_screenshots": False,
        "dump_videos": False
    }

    if not os.path.isfile(configfile):
        with open(configfile, "w", encoding="utf-8") as f:
            config.write(f)
        print("*** created new configuration. please edit ''.".format(configfile))
        if sys.platform == "win32":
            x = input("Press ENTER to exit.")
            sys.exit(1)

    config.read(configfile)

    main(config)

    print("")
    print("Done.")
    if sys.platform == "win32":
        x = input("Press ENTER to exit.")
