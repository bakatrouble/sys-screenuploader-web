import json

from django.core.management import BaseCommand

from app.models import TitleEntry


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('title_db.json') as f:
            data = json.load(f)

        TitleEntry.objects.filter(custom=False).delete()
        entries = []
        for title in data:
            entries.append(TitleEntry(name=title['name'], hash=title['hash'], custom=False))
        TitleEntry.objects.bulk_create(entries)
        print(f'Created {len(entries)} entries')
