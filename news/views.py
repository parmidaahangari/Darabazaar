from django.shortcuts import render
from django.views import View
from .models import News

class NewsView(View):
    def get(self, request):
        news = News.objects.all()
        context = {
            'news': news
        }

        return render(request, 'newspage/news.html', context)

