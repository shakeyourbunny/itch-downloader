import json
import os
import sys
from http.cookiejar import MozillaCookieJar

import dateparser
import requests
import requests.cookies
from bs4 import BeautifulSoup

import config
import dltool

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
                    downloadid = u.find("a")["data-upload_id"]
                    dlurl_final = dlurl + "/file/" + downloadid
                    dlr = session.post(dlurl_final, params=paramPost, data=csfrToken)
                    if dlr.status_code == 200:
                        dljson = dlr.json()
                        if dljson["url"].split("/")[2] == "w3g3a5v6.ssl.hwcdn.net":
                            # remote file check
                            dlhead = session.head(dljson["url"])
                            dldate = dlhead.headers["last-modified"]
                            dlfilename = dlhead.headers["content-disposition"].split('"')[1]
                            dlsize = dlhead.headers["content-length"]

                            # local preparation
                            fulldldir = os.path.join(config.dlbasedir, gamedirectory)
                            os.makedirs(fulldldir, exist_ok=True)
                            fulldname = os.path.join(fulldldir, dlfilename)
                            do_download = True

                            # local file check
                            print("Downloading '{}', {} Bytes.".format(dlfilename, dlsize))
                            completed_key = dlurl + " " + dlfilename

                            # file sanity checks of completed downloads
                            if completed_key in completed_downloads:
                                if dlsize == completed_downloads[completed_key]["size"] and dldate == \
                                        completed_downloads[completed_key]["date"]:
                                    do_download = False
                                else:
                                    if os.path.isfile(fulldname):
                                        if os.path.getsize(fulldname) != dlsize:
                                            print(" -> redownloading, online and local files have different sizes!")
                                            do_download = True
                                        elif os.stat(dlfilename).st_mtime != dateparser.parse(dldate):
                                            print(
                                                " -> redownloading, online and local files have different timestamps!")
                                            do_download = True
                                    else:
                                        print("-> redownloading, file has vanished?")
                                        do_download = True

                            if do_download:
                                if dltool.download_a_file(dljson["url"], filename=fulldname, session=session):
                                    completed_downloads[dlurl + " " + dlfilename] = {
                                        "title": g["title"],
                                        "filename": dlfilename,
                                        "homepage": dlurl,
                                        "url": g["dlurl"],
                                        "developer": dlurl.split("/")[2],
                                        "id": downloadid,
                                        "size": dlsize,
                                        "date": dldate
                                    }
                                with open(os.path.join(config.dlbasedir, config.datalib_completed_downloads), "w",
                                          encoding="utf-8") as f:
                                    json.dump(completed_downloads, f)
                                f.close()
                            else:
                                print("-> skipping, already downloaded.")
                        else:
                            print("*** STOP not implemented. ***")
                            print(g)
                            sys.exit(1)

                        dlfilename = dljson["url"].rsplit("/", 1)[1].replace("/", "_").rsplit("?", 1)[0]
                        print("")
                    else:
                        print("Error on POSTing '{}' [{}].".format(dlurl_final, dlr.status_code))
                        sys.exit(1)
            else:
                print("Could not access download page {} !".format(g["dlurl"]))
                sys.exit(1)



    else:
        print("Could not access {} properly [{}].".format(mypurchases_url, r.status_code))

if __name__ == "__main__":
    main()
