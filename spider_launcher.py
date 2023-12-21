import requests
from concurrent.futures import ThreadPoolExecutor

SCRAPYD_API_URL = "http://localhost:6800"
PROJECT_NAME = "imagegrabber"
SPIDER_NAME = "ImageGrab"

def run_spider(url):
    payload = {
        'project': PROJECT_NAME,
        'spider': SPIDER_NAME,
        'url': url,
    }

    response = requests.post(f"{SCRAPYD_API_URL}/schedule.json", data=payload)
    print(f"Spider for {url} submitted. Job ID: {response.json().get('jobid')}")

def main():
    # List of URLs to scrape re

    # Set the number of threads you want to use
    num_threads = 5

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(run_spider, urls)

if __name__ == "__main__":
    main()
