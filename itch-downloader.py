import json
import os
import sys
from http.cookiejar import MozillaCookieJar

import requests
import requests.cookies
from bs4 import BeautifulSoup

import config
import dltool

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
        dlfilename = dlhead.headers["content-disposition"].split('"')[1]
        dlsize = dlhead.headers["content-length"]

        # local preparation
        fulldldir = os.path.join(config.dlbasedir, gamedirectory)
        os.makedirs(fulldldir, exist_ok=True)
        fulldname = os.path.join(fulldldir, dlfilename)

        # do the download
        dltool.download_a_file(dlj["url"], filename=fulldname, session=session)
    else:
        dldomain = dlj["url"].split("/")[2]
        if dldomain == "drive.google.com":
            print("******** Download from Google Drive is UNSUPPORTED: {}.".format(dlj["url"]))
        else:
            print("")

def main():
    session = requests.Session()
    cookiejar = requests.cookies.RequestsCookieJar()

    cookies = MozillaCookieJar("cookies-itch.txt")
    cookies.load(ignore_expires=True, ignore_discard=True)
    cookiejar.update(cookies)

    session.cookies = cookiejar

    os.makedirs(config.dlbasedir, exist_ok=True)
    print("*** loading completed downloads library.")
    if os.path.isfile(os.path.join(config.dlbasedir, config.datalib_completed_downloads)):
        with open(os.path.join(config.dlbasedir, config.datalib_completed_downloads), "r", encoding="utf-8") as f:
            completed_downloads = json.loads(f.read())
    else:
        completed_downloads = dict()

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
                gamelist.append(
                    {
                        "title": gtitle,
                        "dlurl": gurl
                    }
                )

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

        for g in gamelist:
            print(" -- " + g["title"])

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



    else:
        print("Could not access {} properly [{}].".format(mypurchases_url, r.status_code))

if __name__ == "__main__":
    main()
