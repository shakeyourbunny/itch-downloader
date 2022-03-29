import bs4
import requests
import json
import sys
import threading
import os
import re
import datetime

def downloadGames(inp, allGames):
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
                response = requests.post(i[j]["url"], params = i[j]["params"], data = i[j]["data"], cookies = i[j]["cookies"])
                filename = ""
                if json.loads(response.text)["url"].split("/")[2] == "w3g3a5v6.ssl.hwcdn.net":
                    response = requests.get(json.loads(response.text)["url"], stream = True)
                    refind = re.findall("filename=(.+)", response.headers["content-disposition"])[0]
                    filename = i[j]["url"].rsplit("/", 1)[len(i[j]["url"].rsplit("/", 1))-1] + "_" + refind[1:len(refind)-1].replace("/", "_")
                else:
                    filename = i[j]["url"].rsplit("/", 1)[len(i[j]["url"].rsplit("/", 1))-1] + "_" + json.loads(response.text)["url"].rsplit("/", 1)[1].replace("/", "_")
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
                            sys.stdout.write("\r[%s%s] " % ('=' * done, ' ' * (50-done)) + str(dl) + " of " + str(length))    
                            sys.stdout.flush()
                    file.close()
                print("")

def listingGames(inp, url, posting, item, reqData):
    gameList = [ item ]
    gamesUploaded = []
    urlPost = ""
    paramPost = {}
    cookiesPost = {}
    csfrToken = {}
    if not posting:
        dataGet = requests.get(reqData)
        urlPost = reqData.rsplit("/", 2)[0]
        paramPost = { "source": "game_download", "key": reqData.split("/")[5] }
        cookiesPost = dataGet.cookies
        csfrToken = { "csrf_token": bs4.BeautifulSoup(dataGet.text, "html.parser").find("meta", attrs = { "name": "csrf_token" })["value"] }
        gamesUploaded = bs4.BeautifulSoup(dataGet.text, "html.parser").find("div", class_ = "upload_list_widget").find_all(class_ = "upload")
    else:
        dataPost = requests.post(url, data = reqData[0], cookies = reqData[1])
        urlPost = url.rsplit("/", 2)[0]
        paramPost = { "source": "game_download", "key": url.split("/")[5] }
        cookiesPost = dataPost.cookies
        csfrToken = { "csrf_token": bs4.BeautifulSoup(dataPost.text, "html.parser").find("meta", attrs = { "name": "csrf_token" })["value"] }
        gamesUploaded = bs4.BeautifulSoup(dataPost.text, "html.parser").find("div", class_ = "upload_list_widget").find_all(class_ = "upload")
    if not (os.path.isdir(os.getcwd() + "/" + inp + "/" + gameList[0] + "/") and len(gamesUploaded) == len(os.listdir(os.getcwd() + "/" + inp + "/" + gameList[0] + "/"))):
        for game in range(0, len(gamesUploaded)):
            try:
                uploadId = gamesUploaded[game].find("a")["data-upload_id"]
                gameList.append({ "url": urlPost + "/file/" + uploadId, "params": paramPost, "data": csfrToken, "cookies": cookiesPost })
                print(gameList[0] + " =>", gameList[len(gameList)-1]["url"])
            except TypeError:
                gameList.append({ "lookatUrl": url, "lookatPost": urlPost, "id": (game + 1) })
                print(gameList[0] + " => Look At " + str(game))
        return gameList
    else:
        print(gameList[0] + " =# Has already been downloaded")
        return None

def main():
    print("Please input bundle from itch.io (only the id of the url, not with the actual)")
    inp = input()
    url = "https://itch.io/bundle/download/" + inp
    r = requests.get(url)
    if r.ok and r.status_code == 200:
        allGamesId = []
        pages = int(bs4.BeautifulSoup(r.text, "html.parser").find("span", class_ = "pager_label").a.get_text())
        for i in range(1, pages + 1):
            print("PAGE: {} of {}".format(i, pages))
            r = requests.get(url + "?page=" + str(i))
            if r.ok and r.status_code == 200:
                findingSoup = bs4.BeautifulSoup(r.text, "html.parser").find("div", class_ = "game_list").find_all(class_ = "game_row")
                for gamesList in findingSoup:
                    findingDownload = gamesList.find("a", class_ = "game_download_btn")
                    if findingDownload != None:
                        # get
                        listingG = listingGames(inp, url, False, gamesList.find("h2", class_ = "game_title").get_text(), findingDownload["href"])
                        if not listingG == None:
                            allGamesId.append(listingG)
                        continue
                    
                    findingDownload = gamesList.find("form", class_ = "form")
                    if findingDownload != None:
                        # post
                        inpFinding = findingDownload.find_all("input")
                        butFinding = findingDownload.find("button", class_ = "button")
                        listingG = listingGames(inp, url, True, gamesList.find("a")["href"], [{ inpFinding[0]["name"]: inpFinding[0]["value"], inpFinding[1]["name"]: inpFinding[1]["value"], butFinding["name"]: butFinding["value"] }, r.cookies])
                        if not listingG == None:
                            allGamesId.append(listingG)
                        continue
                        
                    print("FAILED")
                    sys.exit(1)
            else:
                print("ERROR")
        downloadGames(inp, allGamesId)
        print("FINISHED!")
    else:
        print("FAILED TO GET BUNDLE")

if __name__ == "__main__":
    main()
