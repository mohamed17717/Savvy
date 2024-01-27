from django.contrib import admin

from App import models
from silk import models as silky_models


admin.site.register(models.BookmarkFile)
admin.site.register(models.Bookmark)
admin.site.register(models.ScrapyResponseLog)
admin.site.register(models.BookmarkWebpage)
admin.site.register(models.WebpageMetaTag)
admin.site.register(models.WebpageHeader)
admin.site.register(models.DocumentWordWeight)
admin.site.register(models.Cluster)
admin.site.register(models.Tag)

admin.site.register(silky_models.Request)
admin.site.register(silky_models.Response)
admin.site.register(silky_models.SQLQuery)
admin.site.register(silky_models.Profile)