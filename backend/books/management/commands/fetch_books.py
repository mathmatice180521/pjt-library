from django.core.management.base import BaseCommand, CommandError
from books.tasks import fetch_and_save_books

class Command(BaseCommand):
    help = "Fetch books from Aladin API and save to DB."

    def handle(self, *args, **options):
        fetch_and_save_books()
        self.stdout.write(self.style.SUCCESS("[fetch_books] done"))
