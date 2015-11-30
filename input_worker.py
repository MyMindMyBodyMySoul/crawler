from queue_manager import QueueClient
import requests, zipfile, StringIO, shutil, time, datetime

__author__ = 'david'

alexa_splits = [1000000, 1000, 100]
nextDownloadDate = datetime.date.today()

# creates list from AlexaCSV with dated sources
def datedAlexaCSV(splits):
    date = getAlexaCSV()
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
    updateDownloadDate()
    #downloads from url
    r = requests.get("http://s3.amazonaws.com/alexa-static/top-1m.csv.zip")
    print("Finished downloading alexa top 1 million zip. Starting extraction...")
    #unzips
    z = zipfile.ZipFile(StringIO.StringIO(r.content))
    z.extractall()
    print("Finished extracting alexa top 1 million zip. Sending list to queue_manager...")
    #moves file from "crawler" to "crawler/data"
    shutil.move("top-1m.csv", "data/top-1m.csv")
    #get date as "dd.mm.yyyy"
    today = time.strftime("%d.%m.%Y")
    return today

def updateDownloadDate():
    now = datetime.datetime.today()#get todays date
    day = getattr(now, 'day')#get todays day
    month = getattr(now, 'month')#get todays month
    year = getattr(now, 'year')#get todays year
    if day > 20:#day > 20 -> new list will be available on 20th next month
        month = month + 1
        if month > 12:
            month = 1
            year = year + 1
    day = 20
    nextDownloadDate = datetime.date(year,month,day)#creating a datetime.date object that tells, when to download a new list


if __name__ == "__main__":
    # get instance of QueueClient
    c = QueueClient()
    # get appropriate queue from QueueClient
    queue_manager = c.queue_manager()
    queue_manager.put_new_list(datedAlexaCSV(alexa_splits))
    while(True):
        t = datetime.datetime.today()#converting datetime.datetime.today object into datetime.date object
        today = datetime.date(t.year,t.month,t.day)#converting datetime.datetime.today object into datetime.date object
        if today > nextDownloadDate:
            alexa_splits = [1000000, 1000, 100] #2. try crashes without this line at " m = splits[len(splits) - 1] + 1" ~ Line 13
            queue_manager.put_new_list(datedAlexaCSV(alexa_splits))
        print("sleeping now")
        time.sleep(86400)#sleeps for 86400 seconds, ~1 day



