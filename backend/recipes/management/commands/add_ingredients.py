import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('csv_file', nargs='+', type=str)

    def handle(self, *args, **options):
        for csv_file in options['csv_file']:
            datareader = csv.reader(open(csv_file,
                                         encoding='utf-8'),
                                    delimiter=',', quotechar='"')
            for row in datareader:
                ingredient = Ingredient(name=row[0], measurement_unit=row[1])
                ingredient.save()
