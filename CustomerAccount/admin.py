from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(User)
admin.site.register(Order)
admin.site.register(OrderDetail)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(UserAddress)

