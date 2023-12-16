
# Split tasks

## tasks for now

1. App/views.py
   - upload file (html/json)
2. App/signals.py
   1. extract urls from file
   2. create bookmarks & save them
   3. call tasks for crawl bookmarks
   4. store task id in the bookmark file
3. App/tasks.py
   1. call subprocess that run scrapy command
4. crawler/spiders/bookmarks.py
   1. start crawl item
   2. pipeline
      1. write webpage/meta tags/headers
      2. store bookmarks weight word_vector/tags (Success crawled)
   3. middleware
      1. write scrapy_response_log
      2. store bookmarks weight word_vector/tags (Failed crawled)
   4. cluster bookmarks

## Tasks

1. extract bookmarks
2. store bookmarks
3. call scrapy to crawl bookmarks

4. write webpage/meta/headers
5. store (words/tags)
6. store scrapy response log
