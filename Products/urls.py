from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.ProductsView.as_view(), name='products'),
    path('<slug:slug>/', views.ProductView.as_view(), name='product'),
    path('<str:genre>', views.ProductsGenreView.as_view(), name='products_by_genre'),

    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
