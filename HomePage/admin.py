from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(Trending)
admin.site.register(BestSellers)
admin.site.register(Latest)
admin.site.register(BestDeals)
admin.site.register(Hero)

