# Image and Video Scraper Documentation
## Overview
Both scrapers follow the same structure in Scrapy

- Spiders contain the main scraping logic, and handle the queueing of links to start new scrapes
- Middleware comes before or after the spiders/downloader/etc. This is where there are some processing functions, and where the proxies are inserted.
- Pipeline has the link printer, and sends the yielded image/video links to a TSV file for storage

## Key Files
Settings.py - This has the configuration for the spider
- Most values in here are self explanatory

## Usage
Install all python packages needed using requirements.txt
Install scrapy-rotating-proxies and other scrapy dependencies
Navigate to the spiders folder in the project

Spider command formatting: `scrapy crawl VideoGrab -a url=https://www.pexels.com/videos/`

Scrapy will automatically set “start url” and limit the crawl to the root domain

A TSV file will be generated in the spiders folder of all the crawled links.
