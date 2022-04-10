# download pretty a file

import requests
import os, sys
import time, shutil
import dateparser

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', usepercent = True, decimals = 1, fill = '█'):
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

def download_a_file(url, filename="", session=None, cookies=None, rename_old=True):
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
        datadownloaded = 0
        if filename == "":
            filename = data.headers["content-disposition"].split("'")[-1]
        starttime = time.time()

        # rename old download if necessary
        if os.path.exists(filename):
            print("Renaming {} to {}.".format(filename, filename+".old"))
            os.rename(filename, filename+".old")

        # start download
        print("Starting download of {} (-> {})".format(dlurl, filename))
        with open(filename, "wb") as f:
            dl_finished = False
            with session.get(dlurl, stream=True, cookies=cookies) as downloaddata:
                for chunk in downloaddata.iter_content(chunk_size=4096):
                    if chunk:   # filter out keep-alive
                        f.write(chunk)
                        datadownloaded += len(chunk)
                        difftime=time.time()-starttime
                        kbs=(datadownloaded/difftime)/1024
                        mysuffix="{} / {} MB ({} KB/s)".format(round(datadownloaded/1024/1024,1), round(datalength/1024/1024, 1), round(kbs, 1))
                        printProgressBar(datadownloaded, datalength, suffix=filename, prefix=mysuffix, usepercent=False)
        f.close()
        sizeondisk = os.path.getsize(filename)
        #print("\n{} - disk: {}, http: {}".format(filename, sizeondisk, datalength))
        if sizeondisk != datalength:
            print("*** Size on Disk differs from HTTP!!")
            sys.exit(1)
        # touch up timestamp
        timestamp = int(dateparser.parse(dltime).timestamp())
        os.utime(filename, (timestamp, timestamp))

