from django.contrib import admin

from . models import Dataset, Record

admin.site.register(Dataset)
admin.site.register(Record)
