import asyncio
import logging
import time
from typing import Iterable

import scrapy
from bs4 import BeautifulSoup
from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from playwright.async_api import Page
from urllib.parse import urljoin
import re


def imgCompare(curr, new):
    if len(curr) < 2:  # if curr is missing url or size
        return new
    # remove all trailing characters and compare ints

    currSize = int(re.findall("[0-9]*", curr[1])[0])  # match size
    newSize = int(re.findall("[0-9]*", new[1])[0])  # match size

    if newSize > currSize:
        return new
    else:
        return curr


video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.3gp', '.ogg', '.mpeg', '.mpg', '.rm',
                    '.rmvb', '.m4v', '.vob', '.ts', '.divx']
yt_dlp_supported = ["abc", "abcnews", "abcotvs", "abematv", "academicearth", "acast", "acfun", "adn", "adobeconnect",
                    "adobepass", "adobetv", "adultswim", "aenetworks", "aeonco", "afreecatv", "agora", "airtv",
                    "aitube", "aliexpress", "aljazeera", "allocine", "allstar", "alsace20tv", "altcensored", "alura",
                    "amara", "amazon", "amazonminitv", "amcnetworks", "americastestkitchen", "amp", "anchorfm", "angel",
                    "antenna", "anvato", "aol", "apa", "aparat", "appleconnect", "applepodcasts", "appletrailers",
                    "archiveorg", "arcpublishing", "ard", "arkena", "arnes", "arte", "atresplayer", "atscaleconf",
                    "atvat", "audimedia", "audioboom", "audiodraft", "audiomack", "audius", "awaan", "aws", "axs",
                    "azmedien", "baidu", "banbye", "bandaichannel", "bandcamp", "bannedvideo", "bbc", "beatbump",
                    "beatport", "bellmedia", "berufetv", "bet", "bfi", "bfmtv", "bibeltv", "bigflix", "bigo", "bild",
                    "bilibili", "biobiochiletv", "bitchute", "blackboardcollaborate", "bleacherreport", "blerp",
                    "blogger", "bloomberg", "bokecc", "bostonglobe", "box", "boxcast", "bpb", "br", "brainpop",
                    "bravotv", "breitbart", "brightcove", "brilliantpala", "bundesliga", "bundestag", "businessinsider",
                    "buzzfeed", "byutv", "c56", "cableav", "callin", "caltrans", "camdemy", "camfm", "camtasia",
                    "canal1", "canalalpha", "canalc2", "canalplus", "caracoltv", "cartoonnetwork", "cbc", "cbs",
                    "cbsinteractive", "cbsnews", "cbssports", "ccc", "ccma", "cctv", "cellebrite", "ceskatelevize",
                    "cgtn", "charlierose", "chilloutzone", "chingari", "cinemax", "cinetecamilano", "cineverse",
                    "ciscolive", "ciscowebex", "cjsw", "clipchamp", "clippit", "cliprs", "closertotruth",
                    "cloudflarestream", "clubic", "clyp", "cmt", "cnbc", "cnn", "comedycentral", "common",
                    "commonmistakes", "commonprotocols", "condenast", "contv", "corus", "coub", "cozytv", "cpac",
                    "cracked", "crackle", "craftsy", "crooksandliars", "crowdbunker", "crtvg", "crunchyroll", "cspan",
                    "ctsnews", "ctv", "ctvnews", "cultureunplugged", "curiositystream", "cwtv", "cybrary", "dacast",
                    "dailymail", "dailywire", "damtomo", "daum", "daystar", "dbtv", "dctp", "deezer", "democracynow",
                    "detik", "deuxm", "dfb", "dhm", "digg", "digitalconcerthall", "digiteka", "discogs", "discovery",
                    "discoverygo", "disney", "dispeak", "dlf", "dlive", "douyutv", "dplay", "drbonanza", "dreisat",
                    "drooble", "dropbox", "dropout", "drtv", "dtube", "duboku", "dumpert", "duoplay", "dvtv", "dw",
                    "eagleplatform", "ebaumsworld", "ebay", "egghead", "eighttracks", "einthusan", "eitb", "elonet",
                    "elpais", "eltrecetv", "embedly", "epicon", "epidemicsound", "eplus", "epoch", "ertgr", "espn",
                    "ettutv", "europa", "europeantour", "eurosport", "euscreen", "expressen", "extractors", "eyedotv",
                    "facebook", "fancode", "faz", "fc2", "fczenit", "fifa", "filmmodu", "filmon", "filmweb", "firsttv",
                    "fivetv", "flickr", "floatplane", "folketinget", "footyroom", "formula1", "fox", "fox9", "foxnews",
                    "foxsports", "fptplay", "franceinter", "francetv", "freesound", "freespeech", "freetv",
                    "frontendmasters", "fujitv", "funimation", "funk", "funker530", "fuyintv", "gab", "gaia",
                    "gameinformer", "gamejolt", "gamespot", "gamestar", "gaskrank", "gazeta", "gdcvault", "gedidigital",
                    "genericembeds", "genius", "gettr", "giantbomb", "giga", "gigya", "glide", "globalplayer", "globo",
                    "glomex", "gmanetwork", "go", "godtube", "gofile", "golem", "googledrive", "googlepodcasts",
                    "googlesearch", "goplay", "gopro", "gotostage", "gputechconf", "gronkh", "groupon", "harpodeon",
                    "hbo", "hearthisat", "heise", "hgtv", "hidive", "historicfilms", "hitrecord", "hketv",
                    "hollywoodreporter", "holodex", "hotnewhiphop", "hotstar", "hrefli", "hrfensehen", "hrti", "hse",
                    "huajiao", "huffpost", "hungama", "huya", "hypem", "hypergryph", "hytale", "icareus",
                    "ichinanalive", "idolplus", "ign", "iheart", "iltalehti", "imdb", "imggaming", "imgur", "ina",
                    "inc", "indavideo", "infoq", "instagram", "internazionale", "internetvideoarchive", "iprima",
                    "iqiyi", "islamchannel", "israelnationalnews", "itprotv", "itv", "ivi", "ivideon", "ixigua",
                    "izlesene", "jamendo", "japandiet", "jeuxvideo", "jiosaavn", "jixie", "joj", "joqrag", "jove",
                    "jstream", "jtbc", "jwplatform", "kakao", "kaltura", "kanal2", "kankanews", "karaoketv",
                    "karrierevideos", "kelbyone", "khanacademy", "kick", "kicker", "kickstarter", "kinja", "kinopoisk",
                    "kommunetv", "kompas", "konserthusetplay", "koo", "krasview", "kth", "ku6", "kusi", "kuwo", "la7",
                    "lastfm", "laxarxames", "lbry", "lci", "lcp", "lecture2go", "lecturio", "leeco", "lefigaro", "lego",
                    "lemonde", "lenta", "libraryofcongress", "libsyn", "lifenews", "likee", "limelight", "linkedin",
                    "liputan6", "listennotes", "litv", "livejournal", "livestream", "livestreamfails", "localnews8",
                    "lrt", "lumni", "lynda", "maariv", "magellantv", "magentamusik360", "mailru", "mainstreaming",
                    "malltv", "mangomolo", "manoto", "manyvids", "maoritv", "markiza", "massengeschmacktv", "masters",
                    "matchtv", "mbn", "mdr", "medaltv", "mediaite", "mediaklikk", "medialaan", "mediaset", "mediasite",
                    "mediastream", "mediaworksnz", "medici", "megaphone", "megatvcom", "meipai", "melonvod",
                    "metacritic", "mgtv", "miaopai", "microsoftembed", "microsoftstream", "microsoftvirtualacademy",
                    "mildom", "minds", "ministrygrid", "minoto", "mirrativ", "mirrorcouk", "mit", "mitele", "mixch",
                    "mixcloud", "mlb", "mlssoccer", "mocha", "mojvideo", "monstercat", "morningstar", "motorsport",
                    "moviepilot", "moview", "moviezine", "movingimage", "msn", "mtv", "muenchentv", "museai",
                    "musescore", "musicdex", "mxplayer", "myspace", "myspass", "myvideoge", "mzaalo", "n1", "nate",
                    "nationalgeographic", "naver", "nba", "nbc", "ndr", "ndtv", "nebula", "nekohacker", "nerdcubed",
                    "neteasemusic", "netverse", "newgrounds", "newspicks", "newsy", "nextmedia", "nexx", "nfb",
                    "nfhsnetwork", "nfl", "nhk", "nhl", "nick", "niconico", "ninecninemedia", "ninenow", "nintendo",
                    "nitter", "nobelprize", "noice", "noovo", "nosnl", "nova", "novaplay", "nowness", "noz", "npo",
                    "npr", "nrk", "nrl", "ntvcojp", "ntvde", "ntvru", "nuevo", "nytimes", "nzherald", "nzonscreen",
                    "nzz", "odatv", "odkmedia", "odnoklassniki", "oftv", "oktoberfesttv", "olympics", "on24", "once",
                    "onefootball", "onenewsnz", "oneplace", "onet", "onionstudios", "opencast", "openload", "openrec",
                    "ora", "orf", "outsidetv", "owncloud", "packtpub", "palcomp3", "panopto", "paramountplus", "parler",
                    "parlview", "pbs", "pearvideo", "peertube", "peertv", "peloton", "performgroup", "periscope",
                    "pgatour", "philharmoniedeparis", "phoenix", "photobucket", "piapro", "piaulizaportal", "piksel",
                    "pinkbike", "pinterest", "pladform", "planetmarathi", "platzi", "playplustv", "playstuff",
                    "playsuisse", "playtvak", "playwire", "pluralsight", "plutotv", "podbayfm", "podchaser",
                    "podomatic", "pokemon", "pokergo", "polsatgo", "polskieradio", "popcorntimes", "popcorntv",
                    "prankcast", "premiershiprugby", "presstv", "projectveritas", "prosiebensat1", "prx", "puhutv",
                    "puls4", "pyvideo", "qdance", "qingting", "qqmusic", "r7", "radiko", "radiocanada",
                    "radiocomercial", "radiode", "radiofrance", "radiojavan", "radiokapital", "radiozet", "radlive",
                    "rai", "raywenderlich", "rbgtum", "rbmaradio", "rcs", "rcti", "rds", "redbee", "redbulltv",
                    "reddit", "regiotv", "rentv", "restudy", "reuters", "reverbnation", "rheinmaintv", "rinsefm",
                    "rmcdecouverte", "rockstargames", "rokfin", "roosterteeth", "rottentomatoes", "rozhlas", "rte",
                    "rtl2", "rtlnl", "rtnews", "rtp", "rtrfm", "rts", "rtvcplay", "rtve", "rtvs", "rtvslo", "rudovideo",
                    "rumble", "rutube", "rutv", "ruutu", "ruv", "s4c", "safari", "saitosan", "samplefocus", "sapo",
                    "savefrom", "sbs", "sbscokr", "screen9", "screencast", "screencastify", "screencastomatic",
                    "scrippsnetworks", "scte", "seeker", "senalcolombia", "senategov", "sendtonews", "servus",
                    "sevenplus", "seznamzpravy", "shahid", "sharevideos", "shemaroome", "showroomlive", "sibnet",
                    "simplecast", "sina", "sixplay", "sky", "skyit", "skylinewebcams", "skynewsarabia", "skynewsau",
                    "slideshare", "slideslive", "smotrim", "snotr", "sohu", "sonyliv", "soundcloud", "soundgasm",
                    "southpark", "sovietscloset", "spiegel", "spike", "sport5", "sportbox", "sportdeutschland",
                    "spotify", "spreaker", "springboardplatform", "sprout", "srgssr", "srmediathek", "stacommu",
                    "stageplus", "stanfordoc", "startrek", "startv", "steam", "stitcher", "storyfire", "streamable",
                    "streamcz", "streamff", "streetvoice", "stretchinternet", "stv", "substack", "sverigesradio", "svt",
                    "swearnet", "syfy", "syvdk", "sztvhu", "tagesschau", "tass", "tbs", "tbsjp", "tdslifeway",
                    "teachable", "teachertube", "teachingchannel", "teamcoco", "teamtreehouse", "ted", "tele13",
                    "tele5", "telebruxelles", "telecaribe", "telecinco", "telegraaf", "telegram", "telemb", "telemundo",
                    "telequebec", "teletask", "telewebion", "tempo", "tencent", "tennistv", "tenplay", "testurl", "tf1",
                    "tfo", "theguardian", "theholetv", "theintercept", "theplatform", "thestar", "thesun",
                    "theweatherchannel", "thisamericanlife", "thisoldhouse", "threeqsdn", "threespeak", "tiktok", "tmz",
                    "toggle", "toggo", "tonline", "toongoggles", "toutv", "traileraddict", "triller", "trovo",
                    "trtcocuk", "trueid", "trunews", "truth", "trutv", "tubetugraz", "tubitv", "tunein", "turbo",
                    "turner", "tv2", "tv24ua", "tv2dk", "tv2hu", "tv4", "tv5mondeplus", "tv5unis", "tva",
                    "tvanouvelles", "tvc", "tver", "tvigle", "tviplayer", "tvland", "tvn24", "tvnoe", "tvopengr", "tvp",
                    "tvplay", "tvplayer", "tweakers", "twentymin", "twentythreevideo", "twitcasting", "twitch", "udemy",
                    "udn", "ufctv", "ukcolumn", "uktvplay", "umg", "unistra", "unity", "unsupported", "uol", "uplynk",
                    "urort", "urplay", "usanetwork", "usatoday", "ustream", "ustudio", "utreon", "varzesh3", "vbox7",
                    "veo", "vesti", "vgtv", "vh1", "vice", "viddler", "videa", "videocampus_sachsen", "videodetective",
                    "videofyme", "videoken", "videomore", "videopress", "vidio", "vidlii", "vidly", "viewlift",
                    "viidea", "viki", "vimeo", "vimm", "vine", "viqeo", "viu", "vk", "vocaroo", "vodpl", "vodplatform",
                    "voicy", "volejtv", "voot", "voxmedia", "vrt", "vtm", "vuclip", "vvvvid", "walla", "wasdtv",
                    "washingtonpost", "wat", "wdr", "webcamerapl", "webcaster", "webofstories", "weibo", "weiqitv",
                    "weverse", "wevidi", "weyyak", "whowatch", "whyp", "wikimedia", "wimbledon", "wimtv", "wistia",
                    "wordpress", "worldstarhiphop", "wppilot", "wrestleuniverse", "wsj", "wwe", "xboxclips",
                    "xfileshare", "ximalaya", "xinpianchang", "xminus", "xstream", "yahoo", "yandexdisk", "yandexmusic",
                    "yapfiles", "yappy", "yle_areena", "youku", "younow", "yourupload", "zaiko", "zapiks", "zattoo",
                    "zdf", "zee5", "zeenews", "zhihu", "zingmp3", "zoom", "zype"]


class VideograbSpider(CrawlSpider):
    name = "VideoGrab"
    allowed_domains = ["www.pexels.com"]
    # start_urls = ["https://www.pexels.com/videos/"]
    start_urls = ["https://www.pexels.com/video/woman-with-christmas-cookies-5791995/"]

    rules = (
        # Rule(LinkExtractor(), callback='parse_page', follow=True),
    )

    def __init__(self, url="", *args, **kwargs):
        super(VideograbSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url]
        # allow only the subdomain.domain.tld
        self.allowed_domains = [url.split("/")[2]]
        logging.info(f"Starting with {self.start_urls[0]}")
        logging.info(f"Allowed domains: {self.allowed_domains[0]}")

    def start_requests(self) -> Iterable[Request]:
        # for url in self.start_urls:
        #     yield Request(url, dont_filter=True)
        yield Request(self.start_urls[0], dont_filter=True,
                      meta={
                          'playwright': True,
                          'playwright_include_page': True,
                          'playwright_include_page_content': True
                      },
                      callback=self.parse_page
                      )

    async def parse_page(self, response: scrapy.http.Response):
        logging.info(f"PARSING PAGE: {response.url} -----------------------------------------------------------------")
        page: Page = response.meta["playwright_page"]
        topStart = "/".join(response.url.split("/")[:3])


        """ pexels logic:
        the page contains infinite videos, with links
        they then lead to vimeo links
        grab all pexels video links
        output vimeo URLs
        """

        # implement the infinite scrolling logic here
        for i in range(0, 20):
            await page.mouse.wheel(0, 100000000000)
            await asyncio.sleep(0.1)

        time.sleep(3)

        content = await page.content()

        logging.info(f"Parse page: {response.url}")
        soup = BeautifulSoup(content, 'html.parser')

        # use regex to find all urls or src or href etc. in the page content

        # all hrefs
        # hrefs = re.findall(r'href=[\'"]?([^\'" >]+)', content)
        # logging.info(f"Found {len(hrefs)} hrefs")
        # logging.info(hrefs)
        # # all srcs
        # srcs = re.findall(r'src=[\'"]?([^\'" >]+)', content)
        # logging.info(f"Found {len(srcs)} srcs")
        # # all urls
        # urls = re.findall(r'url\([\'"]?([^\'" >]+)', content)
        # logging.info(f"Found {len(urls)} urls")

        ALL_URLS = re.findall(r'(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])', content)

        for i in range(len(ALL_URLS)):
            ALL_URLS[i] = ALL_URLS[i][0] + "://" + ALL_URLS[i][1] + ALL_URLS[i][2]

        #deduplicate
        ALL_URLS = list(set(ALL_URLS))

        # merge all lists
        allLinks = ALL_URLS
        logging.info(f"Found {len(allLinks)} links")

        if len(allLinks) == 0:
            raise CloseSpider("No links found")

        # if it is a half link, add the domain
        for i in range(len(allLinks)):
            if not allLinks[i].startswith('http'):
                allLinks[i] = urljoin(response.url, allLinks[i])


        # yield video links to write to file
        leftovers = []
        for link in allLinks:
            if any(ext in link for ext in video_extensions):

                logging.info(link + " is a video")

                yield {
                    'video_url': link,
                    'page_url': response.url,
                }
                continue

            # re.findall("http(?:s)?:\/\/(?:[\w-]+\.)*([\w-]{1,63})(?:\.(?:\w{3}|\w{2}))(?:$|\/)", link) returns the domain
            # check if the domain is in the yt_dlp_supported list
            l = re.findall("http(?:s)?:\/\/(?:[\w-]+\.)*([\w-]{1,63})(?:\.(?:\w{3}|\w{2}))(?:$|\/)", link)
            if l is not None and len(l) > 0 and l[0] in yt_dlp_supported:
                logging.info(link + " is a yt_dlp_supported")

                yield {
                    'video_url': link,
                    'page_url': response.url,
                }
            else:
                logging.info(link + " is a leftover")
                leftovers.append(link)

        # for i in range(len(leftovers)):
        #     logging.info(f"Leftover {i}: {leftovers[i]}")
        # exit()


        # send all other links to the queue
        for link in leftovers:
            yield scrapy.Request(link, meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_include_page_content': True
            },
             callback=self.parse_page
         )


        # imgs = soup.find_all("img")
        #
        # for img in imgs:
        #     # filter out tiny images
        #     # check if src contains logo or svg
        #     if "logo" in img["src"] or "svg" in img["src"]:
        #         continue
        #
        #     # finding largest image
        #     largestUrl = []
        #
        #     sources = img.find_previous_siblings("source")
        #     if len(sources) != 0:
        #         # use sources list first
        #         for source in sources:
        #             largest = source["srcset"].split(" ")[-2:]  # [url, size]
        #             largestUrl = imgCompare(largestUrl, largest)
        #
        #     try:
        #         # fallback to img srcset
        #         largest = img["srcset"].split(" ")[-2:]
        #         largestUrl = imgCompare(largestUrl, largest)
        #     except:
        #         pass
        #
        #     if len(largestUrl) < 2:
        #         # check for src
        #         try:
        #             # fallback to img src
        #             largest = [img["src"], "0"]
        #             largestUrl = imgCompare(largestUrl, largest)
        #         except:
        #             # no src
        #             continue
        #
        #     src = largestUrl[0]
        #     alt = img.get('alt', '')
        #
        #     yield {
        #         'image_url': src,
        #         'alt_text': alt,
        #         'page_url': response.url,
        #     }


        # Extract links using CSS selector
        #
        # links = response.css('a')
        # logging.info(f"Found {len(links)} links")
        # #
        # # # queue up links for crawling
        #
        # for link in links:
        #     href = link.css('::attr(href)').extract_first()
        #     if href is not None:
        #         logging.info(f"Found link: {href}")
        #         # check if it is a domain
        #         if href.startswith('http'):
        #             # check if its the same domain
        #             topLevel = "/".join(href.split("/")[:3])
        #             if topLevel != topStart:
        #                 continue
        #
        #             logging.info(f"yielding link: {href}")
        #             yield scrapy.Request(href, meta={
        #                 'playwright': True,
        #                 'playwright_include_page': True,
        #                 'playwright_include_page_content': True
        #             },
        #                                  callback=self.parse_page
        #                                  )
        #         elif href.startswith('/'):  # check if it is a relative link
        #             # add domain to relative link
        #             href = urljoin(topStart, href)
        #
        #             logging.info(f"yielding link: {href}")
        #             yield scrapy.Request(href, meta={
        #                 'playwright': True,
        #                 'playwright_include_page': True,
        #                 'playwright_include_page_content': True
        #             },
        #                                  callback=self.parse_page
        #                                  )
        #         else:
        #             pass  # some other link type, ignore
        #
        # close page after we're done with it
        await asyncio.sleep(1)
        await page.close()
