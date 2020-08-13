import scrapy
from scrapy import Request
from learn_crawler.items import CnblogsItem
from scrapy.loader import ItemLoader
from learn_crawler.items import ArticleItemLoader

import re
import json
from urllib import parse


class CnblogsSpider(scrapy.Spider):
    name = 'cnblogs'
    allowed_domains = ['www.cnblogs.com/news']
    start_urls = ['https://www.cnblogs.com/news/']

    def parse(self,response):
        post_nodes = response.xpath("//div[@id='post_list']//article[@class='post-item']")[:1]
        for post_node in post_nodes:
            # url这里可以不是完整的,没有域名部分,所以下方request中需要使用parse来补全
            url = response.xpath("//div[@class='post-item-text']/a[@class='post-item-title']/@href").extract_first("")
            if not url.startswith("http"):
                url = "https:" + url
            image_url = response.xpath("//figure/a/img/@src").extract_first("")
            if not image_url.startswith("http"):
                image_url = "https:" + image_url
            yield Request(url=parse.urljoin(response.url,url),meta={"front_image_url":image_url},callback=self.parse_detail,dont_filter=True)
        #下一页逻辑
        # next_url = response.xpath("//div[@class='pager']//a[contains(text(),'>')]/@href").extract_first("")
        # yield Request(url=parse.urljoin(response.url,next_url),callback=self.parse)

    def parse_detail(self,response):
        article_num = re.match(".*?(\d+).*",response.url)
        article_item = CnblogsItem()
        post_id = article_num.group(1)
        if post_id:
            item_loader = ArticleItemLoader(item=CnblogsItem(),response=response)
            item_loader.add_xpath("title","//div[@id='news_title']/a/text()")
            item_loader.add_value("image_url",response.meta.get("front_image_url",""))


            yield Request(url=parse.urljoin(response.url,"/NewsAjax/GetAjaxNewsInfo?contentId=%s")%post_id,
                          meta={"item_loader":item_loader},callback=self.parse_nums,dont_filter=True,)

    def parse_nums(self,response):
        item_loader = response.meta.get("item_loader","")
        j_data = json.loads(response.text)
        read_num = j_data["TotalView"]
        item_loader.add_value("read_num",read_num)
        article_item = item_loader.load_item()

        yield article_item