from time import sleep
import asyncio
import aiofiles
import aiohttp
import bs4
from urllib.parse import urljoin
import re
from threading import Semaphore
import threading

URL_LIST = "urls.txt"
PROXY_FILE = "proxies.txt"
THREADS = 100
OUTFILE = "images.tsv"
MAX_DEPTH = 3
MAX_CONNECTIONS_PER_DOMAIN = 5

# dict of semaphores for top level urls + (proxy)
# {"url + proxy": semaphore}
semaphores = {}


def scrape(url, depth=0):
    global tasks
    global visited
    global images
    global proxies

    print("Running scrape for " + url + " depth: " + str(depth))


    # check if depth is too deep
    if depth > MAX_DEPTH:
        return

    sleep(1 + depth * 2)

    # schedule 5 more tasks
    for i in range(5):
        task = threading.Thread(target=scrape, args=(url, depth + 1))
        tasks.append(task)
        task.start()


    print("Finished scraping " + url + " depth: " + str(depth))


loop = asyncio.get_event_loop()
tasks = []
visited = {}
images = {}
proxies = []


def main():

    # read in urls
    with open(URL_LIST, "r") as f:
        urls = f.read().split("\n")

    for url in urls:
        print("Starting thread for " + url)
        task = threading.Thread(target=scrape, args=(url, 0))
        tasks.append(task)

    for task in tasks:
        task.start()
        print("Started job")
    for task in tasks:
        task.join()

    print("Finished job")


main()