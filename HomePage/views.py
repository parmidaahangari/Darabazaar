from django.shortcuts import render
from django.views import View
from .models import *
from Products.models import Product

class NewsView(View):
    def get(self, request):
        return render(request, 'home_page/news.html')


class HomeView(View):
    def get(self, request):
        trending = Trending.objects.all()
        latests = Product.objects.all().order_by('-id')[:5]
        bestsellers = BestSellers.objects.all()
        bestdeals = BestDeals.objects.all()
        heroes = Hero.objects.all()
        return render(request, "home_page/home.html", {"trending":trending, "latests":latests, "bestdeals":bestdeals, "bestsellers": bestsellers, "heroes":heroes})

class TrendingView(View):
    def get(self, request):
        trending = Trending.objects.all()
        return render(request, "home_page/trending.html", {"trending":trending})