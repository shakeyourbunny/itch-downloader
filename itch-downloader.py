import datetime
import json
import os
import re
import sys
from http.cookiejar import MozillaCookieJar
import dltool

import bs4
import requests
import requests.cookies
from bs4 import BeautifulSoup

def downloadGames(inp, allGames, session):
    path = os.getcwd() + "/" + inp
    if not os.path.isdir(path):
        os.mkdir(path)
    lookatPath = path + "/Lookat.TODO"
    if not os.path.isfile(lookatPath):
        open(lookatPath, "w").close()
    f = open(lookatPath, "a")
    f.write("-" * 10)
    f.write(str(datetime.datetime.now()))
    f.write("-" * 10)
    f.write("\n")
    f.close()
    for i in allGames:
        pathitem = path + "/" + i[0].replace("/", "_")
        if not os.path.isdir(pathitem):
            os.mkdir(pathitem)
        for j in range(1, len(i)):
            if "lookatUrl" in i[j] and "lookatPost" in i[j]:
                f = open(lookatPath, "a")
                for k in i[j].keys():
                    f.write(k + " " + str(i[j][k]) + " ")
                f.write("\n")
                f.close()
            else:
                response = session.post(i[j]["url"], params=i[j]["params"], data=i[j]["data"], cookies=i[j]["cookies"])
                filename = json.loads(response.text)["url"].rsplit("/", 1)[1].replace("/", "_").rsplit("?", 1)[0]
                if json.loads(response.text)["url"].split("/")[2] == "w3g3a5v6.ssl.hwcdn.net":
                    response = session.get(json.loads(response.text)["url"], stream=True)
                    if "Content-Disposition" in response.headers:
                        refind = re.findall("filename=(.+)", response.headers["content-disposition"])[0]
                        filename = i[j]["url"].rsplit("/", 1)[len(i[j]["url"].rsplit("/", 1)) - 1] + "_" + refind[1:len(
                            refind) - 1].replace("/", "_")
                length = response.headers.get("content-length")
                print("Downloading " + i[0] + ": " + filename)
                with open(pathitem + "/" + filename, "wb") as file:
                    if length is None:
                        file.write(response.content)
                    else:
                        dl = 0
                        length = int(length)
                        for data in response.iter_content(chunk_size=4096):
                            dl += len(data)
                            file.write(data)
                            done = int(50 * dl / length)
                            sys.stdout.write(
                                "\r[%s%s] " % ('=' * done, ' ' * (50 - done)) + str(dl) + " of " + str(length))
                            sys.stdout.flush()
                    file.close()
                print("")

def listingGames(inp, url, posting, item, reqData, session):
    gameList = [item]
    gamesUploaded = []
    urlPost = ""
    paramPost = {}
    cookiesPost = {}
    csfrToken = {}
    if not posting:
        dataGet = session.get(reqData)
        urlPost = reqData.rsplit("/", 2)[0]
        paramPost = {"source": "game_download", "key": reqData.split("/")[5]}
        cookiesPost = dataGet.cookies
        csfrToken = {
            "csrf_token": bs4.BeautifulSoup(dataGet.text, "html.parser").find("meta", attrs={"name": "csrf_token"})[
                "value"]}
        gamesUploaded = bs4.BeautifulSoup(dataGet.text, "html.parser").find("div",
                                                                            class_="upload_list_widget").find_all(
            class_="upload")
    else:
        dataPost = session.post(url, data=reqData[0], cookies=reqData[1])
        urlPost = url.rsplit("/", 2)[0]
        paramPost = {"source": "game_download", "key": url.split("/")[5]}
        cookiesPost = dataPost.cookies
        csfrToken = {
            "csrf_token": bs4.BeautifulSoup(dataPost.text, "html.parser").find("meta", attrs={"name": "csrf_token"})[
                "value"]}
        gamesUploaded = bs4.BeautifulSoup(dataPost.text, "html.parser").find("div",
                                                                             class_="upload_list_widget").find_all(
            class_="upload")
    if not (os.path.isdir(os.getcwd() + "/" + inp + "/" + gameList[0].replace("/", "_") + "/") and len(
            gamesUploaded) == len(os.listdir(os.getcwd() + "/" + inp + "/" + gameList[0].replace("/", "_") + "/"))):
        for game in range(0, len(gamesUploaded)):
            try:
                uploadId = gamesUploaded[game].find("a")["data-upload_id"]
                gameList.append({"url": urlPost + "/file/" + uploadId, "params": paramPost, "data": csfrToken,
                                 "cookies": cookiesPost})
                print(gameList[0] + " =>", gameList[len(gameList) - 1]["url"])
            except TypeError:
                gameList.append({"lookatUrl": url, "lookatPost": urlPost, "id": (game + 1)})
                print(gameList[0] + " => Look At " + str(game))
        return gameList
    else:
        print(gameList[0] + " =# Has already been downloaded")
        return None

def main():
    session = requests.Session()
    cookiejar = requests.cookies.RequestsCookieJar()

    cookies = MozillaCookieJar("cookies-itch.txt")
    cookies.load(ignore_expires=True, ignore_discard=True)
    cookiejar.update(cookies)

    session.cookies = cookiejar

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
                #print("'{}' is not a game, skipping: {}".format(gtitle, gurl))
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

            soup_gamepage = BeautifulSoup(r.text, "html.parser").find_all("a", class_="thumb_link game_link")
            for game in soup_gamepage:
                gamelist.append(int(game["data-label"].split(":")[1]))

            soup_nextpage = BeautifulSoup(r.text, "html.parser").find("div", attrs={"class": "next_page forward_link"})

        print("")
        print("{} items found: {} downloadable games, {} non-game stuff.".format(len(gamelist)+len(not_a_game_list), len(gamelist), len(not_a_game_list)))
        print("")

        for g in gamelist:
            print(" -- "+g["title"])

            r = session.get(g["dlurl"])
            if r.status_code == 200:
                # https://joemanaco.itch.io/captain-backwater/file/12961?source=game_download&key=4zsEYKAs3XzZFDUH_HS_oylA6mpOP_SyNZq5FY_S

                dlpage_soup = BeautifulSoup(r.text, "html.parser")
                dlpage_dlbuttons = dlpage_soup.find_all("a", class_ = "button download_btn")
                dlurl = g['dlurl'].rsplit("/", 2)[0]
                paramPost = {"source": "game_download", "key": g["dlurl"].split("/")[5]}
                csfrToken = dlpage_soup.find("meta", attrs = { "name": "csrf_token"})["value"]
                uploads = dlpage_soup.find("div", class_ = "upload_list_widget").find_all(class_ = "upload")
                for u in uploads:
                    downloadid = u.find("a")["data-upload_id"]
                    dlurl_final = dlurl + "/file/" + downloadid
                    dlr = session.post(dlurl_final, params = paramPost, data = csfrToken )
                    if dlr.status_code == 200:
                        dljson = dlr.json()
                        if dljson["url"].split("/")[2] == "w3g3a5v6.ssl.hwcdn.net":
                            dlhead = session.head(dljson["url"])
                            dldate = dlhead.headers["last-modified"]
                            dlfilename = dlhead.headers["content-disposition"].split('"')[1]
                            dlsize = dlhead.headers["content-length"]
                            print("Downloading '{}', {} Bytes.".format(dlfilename, dlsize))

                            dltool.download_a_file(dljson["url"], filename=dlfilename, session=session)
                            print("")
                        else:
                            print("*** STOP not implemented. ***")
                            print(g)
                            sys.exit(1)

                        dlfilename = dljson["url"].rsplit("/", 1)[1].replace("/", "_").rsplit("?", 1)[0]
                        print("")
                    else:
                        print("Error on POSTing '{}' [{}].".format(dlurl_final, dlr.status_code))
                        sys.exit(1)
                    print("")
            else:
                print("Could not access download page {} !".format(g["dlurl"]))
                sys.exit(1)



    else:
        print("Could not access {} properly [{}].".format(mypurchases_url, r.status_code))

if __name__ == "__main__":
    main()
