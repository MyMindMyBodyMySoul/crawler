from server.queue_manager import QueueClient
import requests, zipfile, StringIO, time, datetime
import os

alexa_splits = [1000000, 1000, 100]
nextDownloadDate = datetime.date.today()
csvPath = "../data/top-1m.csv"

def datedAlexaCSV(split_list):
    """
    Creates a list of URLs from the Alexa top Million Websites with corresponding dated Sources.

    The Data provided by Alexa is a CSV-file with each line consisting of a number and an URL.

    :param split_list: List of Numbers according to which the Sources are to be divided to. MUST NOT BE EMPTY!
    :return: List of Entries, each a List containing: a String of a Target-URL and a List of Source-Strings.
    """
    date = getAlexaCSV()
    splits = split_list[:]
    splits.sort()
    max_entry = splits[len(splits) - 1] + 1
    ret_list = []
    f = open(csvPath, "r")
    for i in range(1, max_entry):
        if i > splits[0]:
            splits.remove(splits[0])
        count = str(i) + ','
        target = f.readline().replace('\n', '').replace(count, '')
        sources = []
        for s in splits:
            sources.append(date + "AlexaTOP" + str(s))
        ret_list.append([target, sources])
    f.close()
    ret_list.sort()
    return ret_list


# downloads and unzips AlexaCSV and return the date
def getAlexaCSV():
    updateDownloadDate()
    #downloads from url
    r = requests.get("http://s3.amazonaws.com/alexa-static/top-1m.csv.zip")
    print("Finished downloading alexa top 1 million zip. Starting extraction...")
    #unzips
    z = zipfile.ZipFile(StringIO.StringIO(r.content))
    if not os.path.exists("../data/"):
        os.mkdir("../data/")
    z.extractall("../data/")
    print("Finished extracting alexa top 1 million zip. Sending list to queue_manager...")
    #moves file from "crawler" to "crawler/data"
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


def joinLists(listA, listB):
    """
    Joins together two URL-Source-Lists without duplicates.

    ListA is extended by the entries of listB and will be the joined list.
    If the same URL occurs in both lists, that entry's source-list in listB is added to listA .

    :param listA: URL-Source-List. MUST BE SORTED!, MUST NOT BE EMPTY!
    :param listB: URL-Source-List. MUST BE SORTED!, MUST NOT BE EMPTY!
    :return: The joined URL-Source-List.
    """
    a = len(listA) - 1
    b = len(listB) - 1
    while b >= 0:
        if listA[a][0] == listB[b][0]:
            listA[a][1].extend(listB[b][1])
            a -= 1
            b -= 1
        elif listA[a][0] < listB[b][0]:
            listA.insert(a+1, listB[b])
            b -= 1
        else:
            a -= 1
    return listA


def joinListOfLists(CountryLists):
    """
    Merges a whole list of URL-Source-Lists into a single URL-Source-Lists via the joinLists Method.

    :param CountryLists: List of URL-Source-Lists. MUST NOT BE EMPTY!
    :return: The joined URL-Source-List.
    """
    while len(CountryLists) > 1:
        m = len(CountryLists)/2 - 1
        while m >= 0:
            joinLists(CountryLists[m], CountryLists.pop())
            m -= 1
    return CountryLists[0]


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
            queue_manager.put_new_list(datedAlexaCSV(alexa_splits))
        os.remove(csvPath)
        print("sleeping now")
        time.sleep(86400)#sleeps for 86400 seconds, ~1 day


