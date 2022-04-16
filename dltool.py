# download pretty a file

import os
import shutil
import time

import dateparser
import requests

# Print iterations progress
def printProgressBar(iteration, total, prefix='', suffix='', usepercent=True, decimals=1, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        usepercent  - Optoinal  : display percentage (Bool)
        decimals    - Optional  : positive number of decimals in percent complete (Int), ignored if usepercent = False
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """

    # length is calculated by terminal width
    twx, twy = shutil.get_terminal_size()
    length = twx - 1 - len(prefix) - len(suffix) -4
    if usepercent:
        length = length - 6
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)

    # process percent
    if usepercent:
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='', flush=True)
    else:
        print('\r%s |%s| %s' % (prefix, bar, suffix), end='', flush=True)

    # Print New Line on Complete
    if iteration == total:
        print(flush=True)

def download_a_file(url, filename="", session=None, cookies=None, rename_old=True, skip_if_identical=True):
    if cookies == None and session != None:
        cookies = session.cookies
    if session == None:
        session = requests.Session()
    dlurl = url

    # check download if available and metadata
    data = session.head(dlurl)
    if data.status_code == 200:
        dltime = data.headers["last-modified"]
        datalength = int(data.headers["content-length"])

        if os.path.exists(filename) and skip_if_identical:
            stats = os.stat(filename)
            if dateparser.parse(dltime).timestamp() == stats.st_mtime and datalength == stats.st_size:
                print("File {} already fully downloaded and identical to online version, skipping.".format(filename))
                return True

        datadownloaded = 0

        if filename == "":
            filename = data.headers["content-disposition"].split("'")[-1]
        shortfilename = filename.split(os.sep)[-1]
        incompletefilename = filename + ".incomplete"
        starttime = time.time()

        # rename old download if necessary
        if os.path.exists(filename) and rename_old:
            print("Renaming {} to {}.".format(filename, filename + ".old"))
            if os.path.exists(filename + ".old"):
                os.remove(filename + ".old")
            os.rename(filename, filename + ".old")

        # start download
        print("Starting download of {} (-> {})".format(dlurl, filename))
        with open(incompletefilename, "wb") as f:
            with session.get(dlurl, stream=True, cookies=cookies) as downloaddata:
                for chunk in downloaddata.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive
                        f.write(chunk)
                        datadownloaded += len(chunk)
                        difftime = time.time() - starttime
                        kbs = (datadownloaded / difftime) / 1024
                        mysuffix = "{} / {} MB ({} KB/s)".format(round(datadownloaded / 1024 / 1024, 1),
                                                                 round(datalength / 1024 / 1024, 1), round(kbs, 1))
                        printProgressBar(datadownloaded, datalength, suffix=shortfilename, prefix=mysuffix,
                                         usepercent=False)
        f.close()

        # finish download
        os.rename(incompletefilename, filename)

        # check size
        sizeondisk = os.path.getsize(filename)
        # print("\n{} - disk: {}, http: {}".format(filename, sizeondisk, datalength))
        if sizeondisk != datalength:
            print("*** Size on Disk differs from HTTP!!")
            return False

        # touch up timestamp
        timestamp = int(dateparser.parse(dltime).timestamp())
        os.utime(filename, (timestamp, timestamp))

        # done
        return True
    else:
        return False
