import difflib
from typing import Optional
from bs4 import BeautifulSoup
import requests
from django.conf import settings
from django.db import models

# Create your models here.
from django.utils import timezone


class MonitoredPage(models.Model):
    title = models.CharField(max_length=64)
    url = models.URLField(verbose_name="URL to monitor")
    raw = models.BooleanField(default=False,verbose_name="Raw content check?", help_text="If checked, will compare unparsed content of url")
    last_check = models.DateTimeField(blank=True, default=None, null=True)
    to_notify = models.ManyToManyField("NotificationDevice", blank=True)

    def __str__(self):
        return f"{self.title} ({self.url})"

    def get_first_diff(self) -> Optional["PageDiff"]:
        diffs = self.pagediff_set.filter(previous__isnull=True)
        if not diffs.exists():
            return None
        elif diffs.count() >1:
            raise Exception("Consistency check failure!")
        else:
            return diffs.get()

    def get_latest_diff(self):
        if self.pagediff_set.exists():
            return self.pagediff_set.latest("created")
        return None

    def update_check_time(self):
        self.last_check = timezone.localtime(timezone.now())
        self.save()

    def monitor(self) -> bool:
        ret = requests.get(self.url)
        content = ret.content
        if not self.raw:
            bs = BeautifulSoup(content, "html.parser")
            content = bs.text
        else:
            content = content.decode("utf8")
        latest = self.get_latest_diff()

        self.update_check_time()

        if latest is not None and latest.content == content:
            return False  # No change
        else:
            # change
            PageDiff(page=self, previous=latest, content=content, diff=create_diff(latest, content)).save()
            return True

    def notify(self):
        for device in self.to_notify.all():
            device.notify(self.title, self.url)


class PageDiff(models.Model):
    page = models.ForeignKey(MonitoredPage, on_delete=models.CASCADE)
    previous = models.ForeignKey("PageDiff", null=True, blank=True, on_delete=models.CASCADE)
    content = models.TextField()  # Save the response content
    diff = models.TextField(blank=True)  # create diff of last one
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.created}] - {self.page.title}"

    def get_next(self):  # Rather slow with many db lookups
        diffs = self.pagediff_set.all()
        count = diffs.count()
        if count == 0:
            return None
        elif count > 1:
            raise Exception("Consistency check failure!")
        else:
            return diffs.get()


class NotificationDevice(models.Model):
    name = models.CharField(max_length=64)
    device_id = models.CharField(max_length=64)

    def notify(self, title, url):
        payload = {  # Set POST fields here
            "t": "URL content changed!",
            "m": f"Content of {title} changed!",
            "c": "#FF0000",
            "d": self.device_id,
            "u": url,
            "ut": title,
            "k": settings.PUSHSAFER_KEY
        }
        url = "https://www.pushsafer.com/api"
        return requests.post(url, data=payload).json()

    def __str__(self):
        return f"{self.name}"

def create_diff(old: Optional[PageDiff], new: str) -> str:
    old_content = old.content if old is not None else ""
    diff = "".join(difflib.unified_diff(old_content, new))
    return diff