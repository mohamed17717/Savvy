# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3


class CrawlerPipeline:
    def process_item(self, item, spider):
        return item


class SQLitePipeline:
    def __init__(self, database_path):
        self.database_path = database_path
        self.conn = sqlite3.connect(database_path)
        self.cursor = self.conn.cursor()
        self.init_database()

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        database_path = settings.get('DATABASE_PATH')

        return cls(database_path)

    def init_database(self):
        # Create a table to store URL status and file paths
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY,
            url TEXT,
            page_title TEXT,
            meta_tags TEXT,
            headers TEXT
        )''')
        self.conn.commit()

    def process_item(self, item, spider):
        meta_tags = item.get('meta_tags', [])
        headers = item.get('headers', [])
        url = item['url'][0]
        page_title = item['page_title'][0]

        # Insert data into the database
        self.cursor.execute(
            "INSERT INTO bookmarks (url, page_title, meta_tags, headers) VALUES (?, ?, ?, ?)",
            (url, page_title, str(meta_tags), str(headers))
        )
        self.conn.commit()

        return item

    def close_spider(self, spider):
        self.conn.close()
