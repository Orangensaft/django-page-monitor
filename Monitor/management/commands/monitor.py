from django.core.management.base import BaseCommand
from Monitor.models import MonitoredPage

class Command(BaseCommand):
    help = 'Checks all saved pages for changes'

    def handle(self, *args, **options):
        changed = 0
        for page in MonitoredPage.objects.all().iterator():
            ret = page.monitor()
            if ret:
                changed+=1
                print(f"{page.title} has changed!")
                #todo: add notification here
            else:
                print(f"{page.title} unchanged.")
        print(f"Done checking all pages. Changes: {changed}")