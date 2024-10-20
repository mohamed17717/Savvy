from django.contrib import admin

from App import models

admin.site.register(models.BookmarkFile)
admin.site.register(models.Bookmark)
admin.site.register(models.ScrapyResponseLog)
admin.site.register(models.BookmarkWebpage)
admin.site.register(models.WebpageMetaTag)
admin.site.register(models.WebpageHeader)
admin.site.register(models.Tag)
admin.site.register(models.Website)
