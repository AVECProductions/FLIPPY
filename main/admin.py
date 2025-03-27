from django.contrib import admin
from .models import ActiveScanner, Keyword, Listing

admin.site.register(ActiveScanner)
admin.site.register(Keyword)
admin.site.register(Listing)