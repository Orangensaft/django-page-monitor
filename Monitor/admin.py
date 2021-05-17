from django.contrib import admin

# Register your models here.
from Monitor.models import PageDiff, MonitoredPage


class PageDiffAdmin(admin.ModelAdmin):
    readonly_fields = ("content", "diff", "previous", "page", "created")
    list_filter = ("page",)
    list_display = ("get_title", "get_url", "created")
    search_fields = ("page__title", "page__url")

    def get_title(self, obj):
        return obj.page.title

    def get_url(self, obj):
        return obj.page.url


class MonitoredPageAdmin(admin.ModelAdmin):
    readonly_fields = ("last_check", )
    list_display = ("title", "url", "last_check")
    search_fields = ("title", "url")

admin.site.register(MonitoredPage, MonitoredPageAdmin)
admin.site.register(PageDiff, PageDiffAdmin)
