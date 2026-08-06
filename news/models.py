from django.db import models
from django.utils import timezone


def news_cover_upload_path(instance, filename):
    return f'news/{filename}'


class News(models.Model):
    title = models.CharField(max_length=100)
    cover_news =  models.ImageField(upload_to=news_cover_upload_path, blank=True, null=True)
    alt_img = models.CharField(max_length=50)
    description = models.TextField(blank=True, default='')
    date = models.DateField(default=timezone.now)