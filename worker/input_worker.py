from server.queue_manager import QueueClient
import requests, zipfile, StringIO, time, datetime
import os
import urllib, multiprocessing
from lxml import etree

alexa_splits = [1000000, 1000, 100]
nextDownloadDate = datetime.date.today()
csvPath = os.path.join(os.path.dirname(__file__),'..','data','top-1m.csv')
dataFolder = os.path.join(os.path.dirname(__file__),'..','data')

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


def getAlexaCSV():
    """
    Downloads the alexa top 1 million list.

    :return: Todays date
    """
    updateDownloadDate()
    #downloads from url
    r = requests.get("http://s3.amazonaws.com/alexa-static/top-1m.csv.zip")
    print("Finished downloading alexa top 1 million zip. Starting extraction...")
    #unzips
    z = zipfile.ZipFile(StringIO.StringIO(r.content))
    #checks if folder "data" exists, will be created if not
    if not os.path.exists(dataFolder):
        os.mkdir(dataFolder)
    z.extractall(dataFolder)
    print("Finished extracting alexa top 1 million zip. Building list...")
    #get date as "dd.mm.yyyy"
    today = time.strftime("%d.%m.%Y")
    return today


def updateDownloadDate():
    """
    Creates a date, that will be used to check if a new version of the alexa top-1m.csv is available.
    The new list should be available on 20th every month.

    Changes variable nextDownloadDate to the date, when a new list should be available.
    """
    now = datetime.datetime.today()
    day = getattr(now, 'day')
    month = getattr(now, 'month')
    year = getattr(now, 'year')
    if day > 20:
        month = month + 1
        if month > 12:
            month = 1
            year = year + 1
    day = 20
    nextDownloadDate = datetime.date(year,month,day)


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
        if a < 0 or listA[a][0] < listB[b][0]:
            listA.insert(a+1, listB[b])
            b -= 1
        elif listA[a][0] == listB[b][0]:
            listA[a][1].extend(listB[b][1])
            listA[a][1].sort()
            a -= 1
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
        m = len(CountryLists)/2
        for i in range(0, m):
            joinLists(CountryLists[i], CountryLists.pop())
    return CountryLists[0]


class DownLoader():
    '''
    Downloader to get all necessary information.
    '''

    def __init__(self, url):
        """
        url contains the url, that will be downloaded.
        contents contains the content of the url, after it is downloaded

        :param url: url, that will be downloaded
        :return: NULL
        """
        self.url = url
        self.contents = ''

    def download(self):
        """
        Creates a browser to get all necessary information. This information will be stored in self.contents
        :return: NULL
        """

        #print self.url
        browser = urllib.urlopen(self.url)
        response = browser.getcode()
        if response == 200: #success
            self.contents = browser.read()


class alexaParser(DownLoader):
    '''
    Class for parsing alexa.com/topsites/countries*
    '''

    def __init__(self,url):
        """

        :param url: url, that will be downloaded
        :return: NULL
        """
        DownLoader.__init__(self,url)
        self.topsiteShort = ''
        self.topsiteName = ''

    def getSiteNames(self):
        """
        Downloads the specified url and fetches the links to all countrie top 500 sites.
        This links will be stored in self.topsiteShort
        :return: NULL
        """
        self.download()
        if self.contents:
            tree = etree.HTML(self.contents)
            self.topsiteShort = tree.xpath("//div/div/ul/li//a/@href")#Get links to contrie sites
            self.topsiteName = tree.xpath("/html/body//div/div/ul/li/a/text()")#Get countrieNames


def getContent(shortName, countrieName, today):
    """
    Fetches all sites in the top 500 for the country with short name shortName.

    :param shortName: The two Letter shortName of the wanted country
    :param countrieName: full name of the country
    :param today: todays date
    :return: a sorted list with all 500 entries as [["url1",[date+countryName]],["url2",[date+countryName]],...]
    """
    parser = alexaParser("")
    sites=[]
    for i in range(0,20):
        if i==0:
            parser.url = "http://www.alexa.com/topsites/countries" + "/" +shortName
            print("Starting to parse country: %s(%s)"%(countrieName, shortName))
        else:
            parser.url = "http://www.alexa.com/topsites/countries" +";"+str(i) +"/"+ shortName
        parser.download()
        if parser.contents:
            tree = etree.HTML(parser.contents)
            topsiteList = tree.xpath("//section/div/ul/li/div/p/a/text()")
            sites.extend(topsiteList)
    sites.sort()
    returnValue=[]
    for url in sites:
                sources = [[url,[today+countrieName]]]
                returnValue.extend(sources)
    return returnValue


def startTop500Parsing():
    """
    Contains all necessary information to start the top 500 parsing.

    :return: returns a multi-dimensional array with all countries and their top 500 websites, as
             a sorted list with all 500 entries as [[["url1",[date+countryName1]],["url2",[date+countryName1]],...],
                                                    [["url1",[date+countryName2]],["url2",[date+countryName2]],...],
                                                                     ...                                         ]

    """
    today = time.strftime("%d.%m.%Y")
    url = "http://www.alexa.com/topsites/countries"
    alexa_parser = alexaParser(url)
    alexa_parser.getSiteNames()
    #fetching shortName out of the link
    for i in range(0,len(alexa_parser.topsiteShort)):
        object = alexa_parser.topsiteShort[i]
        alexa_parser.topsiteShort[i] = object[-2:]
    pool = multiprocessing.Pool(processes=20)
    output = [pool.apply_async(getContent,args=(alexa_parser.topsiteShort[x],alexa_parser.topsiteName[x],today,)) \
              for x in range(0,len(alexa_parser.topsiteShort))]
    results = [p.get() for p in output]
    resultValues = []
    for listComponent in results:
        resultValues.extend([listComponent])
    return resultValues


def fetchInput(queue_manager):
    """
    Downloads top-1m.csv, parses top500 country lists, merges them and sends them to queue_manager.
    """
    top500ListOfLists = startTop500Parsing()
    print("joining top 500 lists")
    top500List = joinListOfLists(top500ListOfLists)
    top1MioList = datedAlexaCSV(alexa_splits)
    print("joining 'joined' top 500 list with alexa top1mio")
    queue_manager.put_new_list(joinLists(top1MioList,top500List))
    print("Finished building and sending list.")


if __name__ == "__main__":
    # get instance of QueueClient
    c = QueueClient()
    # get appropriate queue from QueueClient
    queue_manager = c.queue_manager()
    fetchInput(queue_manager)
    while(True):
        t = datetime.datetime.today()#converting datetime.datetime.today object into datetime.date object
        today = datetime.date(t.year,t.month,t.day)
        if today > nextDownloadDate:
            fetchInput(queue_manager)
        os.remove(csvPath)
        print("sleeping now")
        time.sleep(86400)#sleeps for 86400 seconds, ~1 day


