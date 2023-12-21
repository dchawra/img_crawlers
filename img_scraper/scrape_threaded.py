import concurrent.futures
import queue
import threading
import time
from random import shuffle
from time import sleep
import bs4
from urllib.parse import urljoin
import re
from threading import Semaphore
import logging
from threading import Lock
import requests
import requests_futures
from requests.auth import HTTPProxyAuth

URL_LIST = "urls.txt"
PROXY_FILE = "proxies.txt"
USE_PROXY = True
THREADS = 400
OUTFILE = "images.tsv"
MAX_DEPTH = 10000
MAX_CONNECTIONS_PER_DOMAIN = 5
MAX_SITE_HITS = 100
MAX_TIMEOUT = 5
VISITED_THRESHOLD = 0.90

visitedLock = Lock()
imagesLock = Lock()

# def writer(data):
#     with open(OUTFILE, "a") as f:
#         f.write(data + "\n")
#         f.flush()


def imgCompare(curr, new):
    if len(curr) < 2: # if curr is missing url or size
        return new
    # remove all trailing characters and compare ints

    currSize = int(re.findall("[0-9]*", curr[1])[0]) # match size
    newSize = int(re.findall("[0-9]*", new[1])[0]) # match size

    if newSize > currSize:
        return new
    else:
        return curr

def scrape(url, depth=0):
    startTime = time.time()
    try:
        global visited
        global images
        global proxies
        global logger
        global executor
        global semaphores
        global connectionErrorCount

        # check if depth is too deep
        if depth > MAX_DEPTH:
            return

        # check if i have been rate limited
        if url in visited and visited[url] == -1:
            return

        # check if top level url has semaphore: if so is it maxed out
        # 1) get top level url from "https://url.com/path/to/page" -> "https://url.com"
        topLevel = "/".join(url.split("/")[:3])

        if topLevel not in semaphores:
            semaphores[topLevel] = Semaphore(MAX_CONNECTIONS_PER_DOMAIN)
        semaphores[topLevel].acquire()
        sleep(0.1) # gently !!
        # print("Scraping " + url + " at depth " + str(depth))

        try:
            if USE_PROXY:
                proxy = proxies.get()
                proxies.put(proxy)
                # ip:port:username:password

                internalProxies = {
                    "http": "http://" + proxy
                }

                # print("Using proxy " + proxy)
                response = requests.get(url, proxies=internalProxies, timeout=MAX_TIMEOUT)
            else:
                response = requests.get(url)
        except requests.exceptions.Timeout:
            # print("Timeout detected, exiting scrape...")
            # print("timeout")
            raise requests.exceptions.Timeout
        except requests.exceptions.ConnectionError:
            # likely rate limited, mark visited with -1 to not visit again
            visited[url] = -1
            # print("connection error")
            connectionErrorCount += 1
            raise requests.exceptions.ConnectionError
        except Exception as e:
            # print("Exception detected, exiting scrape...")
            print(type(e))
            raise e
        finally:
            semaphores[topLevel].release() # got response, release semaphore

        page = response.text
        soup = bs4.BeautifulSoup(page, "html.parser")
        imgs = soup.find_all("img")

        with visitedLock:
            # check visited
            if topLevel in visited and visited[topLevel] == -1:
                # print("Rate limited, exiting scrape...")
                return
            elif topLevel in visited and visited[topLevel] >= MAX_SITE_HITS:
                # print("Max site hits, exiting scrape...")
                return

            visited[topLevel] = visited[topLevel] + 1 if topLevel in visited else 1

        for img in imgs:
            if img is None:
                continue

            alt = img.get("alt")
            if alt is None:
                alt = ""
            largestUrl = []

            # finding largest image
            sources = img.find_previous_siblings("source")
            if len(sources) != 0:
                # use sources list first
                for source in sources:
                    largest = source["srcset"].split(" ")[-2:]  # [url, size]
                    largestUrl = imgCompare(largestUrl, largest)

            try:
                # fallback to img srcset
                largest = img["srcset"].split(" ")[-2:]
                largestUrl = imgCompare(largestUrl, largest)
            except:
                pass

            if len(largestUrl) < 2:
                # check for src
                try:
                    # fallback to img src
                    largest = [img["src"], "0"]
                    largestUrl = imgCompare(largestUrl, largest)
                except:
                    # no src
                    continue

            with imagesLock:
                #check images duplicate
                if largestUrl[0] not in images or len(images[largestUrl[0]]) == 0:
                    images[largestUrl[0]] = alt
                    # write to logger
    
                    logger.info(alt + "\t" + urljoin(url, largestUrl[0]) + "\t" + str(depth))
                else:
                    pass # duplicate image

        # find all links on page
        a_tags = soup.find_all("a")

        newJobs = []
        visitedCount = 0

        if len(a_tags) == 0:
            # print("No links found, exiting scrape...")
            return

        for a in a_tags:
            href = a.get("href")
            if href is None:
                continue

            # check for non http links
            if href.startswith("https://") or href.startswith("http://"):
                # # check if its the same domain
                # if href.split("/")[2] != url.split("/")[2]:
                #     print("Duplicate url " + url)
                if href in visited:
                    visitedCount += 1
                    # print("Duplicate url " + href)
                    continue

                newUrl = href
            else:
                joined = urljoin(url, href)
                if joined in visited:
                    visitedCount += 1
                    continue

                if not joined.startswith("http"):
                    continue

                newUrl = joined

            # check depth of new url
            if depth + 1 <= MAX_DEPTH:
                visited[newUrl] = 1

                #add new job
                newJobs.append(newUrl)

        if visitedCount / len(a_tags) > VISITED_THRESHOLD:
            # print("Too many visited links, exiting scrape...")
            return

        # launch new jobs
        for newUrl in newJobs:
            task = threading.Timer(0, scrape, args=[newUrl, depth + 1])
            task.daemon = True
            executor.submit(task.run)

        # print("Finished scraping " + url)
    except KeyboardInterrupt:
        print("Keyboard interrupt detected, exiting scrape...")
    except requests.exceptions.Timeout:
        print("Timeout detected, exiting scrape...")
        global timeoutCount
        timeoutCount += 1

    except requests.exceptions.ConnectionError:
        # print("Connection error detected, exiting scrape...")
        pass
    except Exception as e:
        print("Exception detected, exiting scrape...")
        global exceptionCount
        exceptionCount += 1
        # print traceback
        print(type(e))
        print(e)


def threadWatcher():
    try:
        global executor
        global timeoutCount
        global exceptionCount
        global connectionErrorCount

        startTime = time.time()

        lastTen = []

        while True:
            sleep(1)
            print("Queued threads: " + str(executor._work_queue.qsize()))
            print("Running threads: " + str(threading.active_count() - 1))
            print("Timeouts: " + str(timeoutCount))
            print("Exceptions: " + str(exceptionCount))
            print("Connection errors: " + str(connectionErrorCount))

            # check change in last 10 seconds
            lastTen.append(executor._work_queue.qsize())
            if len(lastTen) > 10:
                lastTen.pop(0)

                same = True
                for i in range(len(lastTen) - 1):
                    if lastTen[i] != lastTen[i + 1]:
                        same = False
                        break
                if same:
                    print("No change in last 10 seconds, kill running threads...")
                    #TODO
                    return

            if executor._work_queue.qsize() == 0:
                print("All threads finished, exiting threadWatcher...")
    except KeyboardInterrupt:
        print("Keyboard interrupt detected, exiting threadWatcher...")

# dict of semaphores for top level urls + (proxy)
# {"url + proxy": semaphore}
semaphores = {}

# make priority queue for proxies
proxies = queue.Queue()
with open(PROXY_FILE, "r") as f:
    allP = f.readlines()
    shuffle(allP)
    for proxy in allP:
        proxies.put(proxy.strip())


visited = {}
images = {}
logger = logging.getLogger('log')
executor = concurrent.futures.ThreadPoolExecutor(max_workers=THREADS)

timeoutCount = 0
exceptionCount = 0
connectionErrorCount = 0

def main():
    try:
        with open(OUTFILE, "w") as f:
            f.write("alt_text\timage_url\tdepth\n")

        logger.setLevel(logging.INFO)
        ch = logging.FileHandler(OUTFILE)
        ch.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(ch)

        with open(URL_LIST, "r") as f:
            urls = f.readlines()
        urls = [url.strip() for url in urls]

        for url in urls:
            visited[url] = 1
            executor.submit(scrape, url, 0)


        print("Finished launching threads")

        # make a watcher thread to check if all threads are done
        watcher = threading.Timer(5, threadWatcher)
        watcher.start()
        watcher.join()

        print("Finished scraping")
    except KeyboardInterrupt:
        print("Keyboard interrupt detected, exiting...")


main()

