from django.urls import path
from . import views
 
urlpatterns = [
    path('dashboard/', views.CustomerAccountView.as_view(), name='dashboard'),

    
]

