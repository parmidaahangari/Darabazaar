from django.db import models
from CustomerAccount.models import Product


class Trending(models.Model):
    product = models.ManyToManyField(Product, blank=True, related_name='trending')
    gameimage = models.ImageField(upload_to='trending', blank=True, null=None, verbose_name="کاور بازی")
    gamebg = models.ImageField(upload_to='trending', blank=True, null=None, verbose_name="پس‌زمینه بازی")
    

class BestSellers(models.Model):
    product = models.ManyToManyField(Product, blank=True, related_name='bestsellers')

class Latest(models.Model):
    product = models.ManyToManyField(Product, blank=True, related_name='latest')
    
class BestDeals(models.Model):
    product = models.ManyToManyField(Product, blank=True, related_name='bestDeals')
     
class Hero(models.Model):
    text = models.TextField(max_length=50, blank=True)
    image = models.ImageField(upload_to='hero', blank=True, null=None, verbose_name="هیرو هوم")
