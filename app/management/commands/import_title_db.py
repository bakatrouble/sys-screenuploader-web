import json

from django.core.management import BaseCommand

from app.models import TitleEntry


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('title_db.json') as f:
            data = json.load(f)

        TitleEntry.objects.all().delete()
        entries = []
        for title in data:
            entries.append(TitleEntry(name=title['name'], hash=title['hash']))
        TitleEntry.objects.bulk_create(entries)
        print(f'Created {len(entries)} entries')
