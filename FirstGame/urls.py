"""
URL configuration for FirstGame project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from CustomerAccount.views import SignupView, LoginView, CustomerCartView, CustomerAdressesViewCheckout
from HomePage.views import TrendingView
from Products.views import SearchSuggestionsView

urlpatterns = [
    path('', include('HomePage.urls')),
    path('admin/', admin.site.urls), # URL امن برای پنل ادمین
    path('my/', include('CustomerAccount.urls')),
    path('products/', include('Products.urls')),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', SignupView.as_view(), name='register'),
    path('trending/', TrendingView.as_view(), name='trending'),
    path('checkout/cart/', CustomerCartView.as_view(), name='cart'),
    path('checkout/addresse/', CustomerAdressesViewCheckout.as_view(), name='addresse'),
    path('checkout/addresses/edit/<int:address_id>/', CustomerAdressesViewCheckout.as_view(), name='checkout_edit_address'),
    path('api/search/suggestions/', SearchSuggestionsView.as_view(), name='search_suggestions'),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

