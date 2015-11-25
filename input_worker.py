from queue_manager import QueueClient
import requests, zipfile, StringIO, shutil, time

__author__ = 'david'

alexa_splits = [1000000, 1000, 100]

# creates list from AlexaCSV with dated sources
def datedAlexaCSV(date, splits):
    splits.sort()
    m = splits[len(splits) - 1] + 1
    r = []
    f = open("data/top-1m.csv", "r")
    for i in range(1,m):
        c = str(i) + ','
        t = f.readline().replace('\n', '').replace(c, '')
        q = []
        for s in splits:
            q.append(date + "AlexaTOP" + str(s))
        r.append([t, q])
        i += 1
        if i > splits[0]:
            splits.remove(splits[0])
    f.close()
    return r


# downloads and unzips AlexaCSV and return the date
def getAlexaCSV():
    #downloads from url
    r = requests.get("http://s3.amazonaws.com/alexa-static/top-1m.csv.zip")
    #unzips
    z = zipfile.ZipFile(StringIO.StringIO(r.content))
    z.extractall()
    #moves file from "crawler" to "crawler/data"
    shutil.move("top-1m.csv", "data/top-1m.csv")
    #get date as "dd.mm.yyyy"
    a = time.strftime("%d.%m.%Y")
    return a


if __name__ == "__main__":

    # get instance of QueueClient
    c = QueueClient()

    # get appropriate queue from QueueClient
    #host_queue = c.host_queue()
    queue_manager = c.queue_manager()
    d = getAlexaCSV()
    #host_queue.put(datedAlexaCSV(d, alexa_splits))
    queue_manager.put_new_list(queue_manager, datedAlexaCSV(d, alexa_splits))



