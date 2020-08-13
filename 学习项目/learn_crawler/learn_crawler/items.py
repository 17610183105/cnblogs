import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join, Identity

class LearnCrawlerItem(scrapy.Item):
    pass


class ArticleItemLoader(ItemLoader):
    #自定义itemloader,用来将itemloader获取的列表只取第一个元素
    default_output_processor = TakeFirst()


class CnblogsItem(scrapy.Item):
    title = scrapy.Field()
    image_url = scrapy.Field(
        # 图片必须是list,所以覆盖自定义的TakeFirst(),还原为列表
        output_processor=Identity()
    )
    image_path = scrapy.Field()
    read_num = scrapy.Field()