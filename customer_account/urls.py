from django.urls import path
from . import views
 
urlpatterns = [
    path('dashboard/', views.CustomerAccountView.as_view(), name='dashboard'),
    path('information/', views.CustomerAccountInfoView.as_view(), name='personal_information'),

    
]

