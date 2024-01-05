# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import logging

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
import random

from scrapy import Request
import base64


class StickyDepthSpiderMiddleware:

    def process_spider_output(self, response, result, spider):
        key_found = response.meta.get('depth', None)
        for x in result:
            if isinstance(x, Request) and key_found is not None:
                x.meta.setdefault('depth', key_found)
            yield x


class videograbberSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class videograbberDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.


        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

# Importing base64 library because we'll need it ONLY in case if the proxy we are going to use requires authentication

# Start your middleware class
class ProxyMiddleware(object):

    def __init__(self, settings):
        # load our proxy list
        filepath = settings.get('PROXY_LIST')
        self.proxies = open(filepath).read().splitlines()

    @classmethod
    def from_crawler(cls, crawler):
        stg = crawler.settings
        return stg

    # overwrite process request
    def process_request(self, request, spider):
        # Set the location of the proxy
        curr = random.choice(self.proxies).split("@")
        request.meta['proxy'] = curr[1]
        logging.info(f"Using proxy***************************************************************************************************: {curr[1]}")

        # Use the following lines if your proxy requires authentication
        proxy_user_pass = curr[0]
        # setup basic authentication for the proxy
        encoded_user_pass = base64.b64encode(proxy_user_pass.encode()).decode()
        request.headers['Proxy-Authorization'] = 'Basic ' + encoded_user_pass


class VerifyProxyMiddleware(object):
    def process_request(self, request, spider):
        # add proxy info to playwright_context_kwargs
        logging.log(logging.INFO, f"Using proxy: {request.meta['proxy']}")

        proxy = request.meta['proxy']

        # separate server, username, password
        proxyserver = "http://" + proxy.split("@")[1]
        proxyuser = proxy.split("@")[0].split("/")[2].split(":")[0] # eqnggryk
        proxypass = proxy.split("@")[0].split("/")[2].split(":")[1] # bhje3uv9fg60

        # add proxy info to playwright_context_kwargs
        # create playwright_context_kwargs if it doesn't exist
        if 'playwright_context_kwargs' not in request.meta:
            request.meta['playwright_context_kwargs'] = {}

        # add proxy info to playwright_context_kwargs
        request.meta['playwright_context_kwargs']['proxy'] = {
            'server': proxyserver,
            'username': proxyuser,
            'password': proxypass
        }
        request.meta['playwright_context_kwargs']['ignore_https_errors'] = True