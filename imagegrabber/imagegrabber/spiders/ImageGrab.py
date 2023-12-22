from typing import Iterable

import scrapy
from bs4 import BeautifulSoup
from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import re


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


class ImagegrabSpider(CrawlSpider):
    name = "ImageGrab"
    allowed_domains = ["www.lacucinaitaliana.it"]
    start_urls = ["https://www.lacucinaitaliana.it/"]

    rules = (
        Rule(LinkExtractor(), callback='parse_page', follow=True),
    )

    def __init__(self, url, *args, **kwargs):
        super(ImagegrabSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url]
        self.allowed_domains = [url.split("/")[:-1]]


    def start_requests(self) -> Iterable[Request]:
        # for url in self.start_urls:
        #     yield Request(url, dont_filter=True)
        yield Request(self.start_urls[0], dont_filter=True,
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_include_page_content': True
            }
        )

    def parse_page(self, response: scrapy.http.Response):
        # Extract image elements using CSS selector
        images = response.css('img')

        soup = BeautifulSoup(response.text, 'html.parser')
        imgs = soup.find_all("img")

        # Iterate over each image element and yield src and alt attributes

        # print response size
        # print(len(response.text))
        #
        # print(len(imgs))
        # print(len(images))


        for img in imgs:
            # filter out tiny images
            # check if src contains logo or svg
            if "logo" in img["src"] or "svg" in img["src"]:
                continue

            # finding largest image
            largestUrl = []

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

            src = largestUrl[0]
            alt = img.get('alt', '')

            yield {
                'image_url': src,
                'alt_text': alt,
                'page_url': response.url,
            }


        # Extract links using CSS selector

        # links = response.css('a')

        # # queue up links for crawling
        # for link in links:
        #     href = link.css('::attr(href)').extract_first()
        #     if href is not None:
        #
        #         # check if it is a domain
        #         if href.startswith('http'):
        #             # check if its the same domain
        #             topLevel = "/".join(url.split("/")[:3])
        #             print(topLevel)
        #             exit()
        #             if topLevel != self.start_urls[0]:
        #                 continue
        #
        #             yield scrapy.Request(href, meta={
        #                 'playwright': True,
        #                 'playwright_include_page': True,
        #                 'playwright_include_page_content': True
        #             })
        #         elif href.startswith('/'): # check if it is a relative link
        #             exit()
        #             yield scrapy.Request(response.urljoin(href), meta={
        #                 'playwright': True,
        #                 'playwright_include_page': True,
        #                 'playwright_include_page_content': True
        #             })
        #         else:
        #             exit()
        #             pass # some other link type, ignore
