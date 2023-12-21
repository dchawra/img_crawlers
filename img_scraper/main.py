from time import sleep
import asyncio
import aiofiles
import aiohttp
import bs4
from urllib.parse import urljoin
import re
from threading import Semaphore

URL_LIST = "urls.txt"
PROXY_FILE = "proxies.txt"
THREADS = 100
OUTFILE = "images.tsv"
MAX_DEPTH = 50
MAX_CONNECTIONS_PER_DOMAIN = 5

# dict of semaphores for top level urls + (proxy)
# {"url + proxy": semaphore}
semaphores = {}

async def writer(data):
    async with aiofiles.open(OUTFILE, "a") as f:
        await f.write(data + "\n")
        await f.flush()

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

async def scrape(url, depth=0):
    global tasks
    global visited
    global images
    global proxies

    print(visited)

    # check if depth is too deep
    if depth > MAX_DEPTH:
        return

    # check if top level url has semaphore: if so is it maxed out
    # 1) get top level url from "https://url.com/path/to/page" -> "https://url.com"
    topLevel = "/".join(url.split("/")[:3])

    if topLevel not in semaphores:
        semaphores[topLevel] = Semaphore(MAX_CONNECTIONS_PER_DOMAIN)
    print("Current connnections for " + topLevel + ": " + str(MAX_CONNECTIONS_PER_DOMAIN - semaphores[topLevel]._value))
    semaphores[topLevel].acquire()
    print("Acquired semaphore for " + topLevel)

    async with (aiohttp.ClientSession() as session):
        async with session.get(url) as response:
            print("Scraping " + url)
            page = await response.text()
            soup = bs4.BeautifulSoup(page, "html.parser")
            imgs = soup.find_all("img")

            visited[url] = True

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

                #check images duplicate
                if largestUrl[0] in images:
                    continue
                else:
                    images[largestUrl[0]] = True
                    # write to queue
                    await writer(alt + "\t" + urljoin(url, largestUrl[0]) + "\t" + str(depth))

            # find all links on page
            a_tags = soup.find_all("a")

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
                        print("Duplicate url " + href)
                        continue

                    print("adding " + href + " to dict")

                    visited[href] = True
                    tasks.append(asyncio.create_task(scrape(href, depth + 1)))
                    print("after await *************************************************** " + href)
                    # await scrape(href, proxy, visited, images, depth + 1)
                else:
                    joined = urljoin(url, href)
                    if joined in visited:
                        print("Duplicate url " + joined)
                        continue

                    print("adding " + joined + " to dict")
                    visited[joined] = True

                    if not joined.startswith("http"):
                        print("Invalid url " + joined)
                        continue
                    tasks.append(asyncio.create_task(scrape(joined, depth + 1)))
                    print("after await *************************************************** " + joined)
    semaphores[topLevel].release()
    print("Finished scraping " + url)


loop = asyncio.get_event_loop()
tasks = []
visited = {}
images = {}
proxies = []
async def main():
    with open(OUTFILE, "w") as f:
        f.write("alt_text\timage_url\tdepth\n")


    with open(URL_LIST, "r") as f:
        urls = f.readlines()
    urls = [url.strip() for url in urls]


    for url in urls:
        print("Starting thread for " + url)
        task = asyncio.create_task(scrape(url, 0))
        print("created first task *************************************************** " + url)
        tasks.append(task)

    await asyncio.gather(*tasks)

    print("Finished job")

loop.run_until_complete(main())
loop.close()



