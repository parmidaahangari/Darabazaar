from django.urls import path
from . import views
 
urlpatterns = [
    path('news/', views.NewsView.as_view() , name='news'),
    path('', views.HomeView.as_view(), name="home"),

]

