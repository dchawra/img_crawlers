import requests

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
    urls = []
    with open("urls.txt", "r") as f:
        urls = f.readlines()

    # submit spiders, no need for threading
    for url in urls[:1]:
        run_spider(url)

if __name__ == "__main__":
    main()
