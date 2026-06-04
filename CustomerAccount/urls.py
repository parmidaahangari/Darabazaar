from django.urls import path
from . import views
from .views import add_new_wishlist


urlpatterns = [
    path('dashboard/', views.CustomerAccountView.as_view(), name='dashboard'),
    path('information/', views.CustomerAccountInfoView.as_view(), name='personal_information'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('wishlist/', views.CustomerWishlistView.as_view(), name='wishlist'),
    path("wishlist/add", add_new_wishlist, name='add_new_wishlist'),
    path('wishlist/remove/', views.RemoveFromWishlistView.as_view(), name='remove_from_wishlist'),

    path('cart/remove/<str:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('cart/add/', views.add_new_cart, name='add-to-cart'),
    
    path('cart/update/<str:item_id>/', views.UpdateCartItemQuantityView.as_view(), name='update_cart_item'),

    path('orders/', views.CustomerOrderView.as_view(), name='orders'),

    path('addresses/', views.CustomerAdressesView.as_view(), name='customer_addresses'),
    path('addresses/<int:address_id>/', views.CustomerAdressesView.as_view(), name='customer_addresses_edit'),
    path('addresses/delete/<int:address_id>/', views.DeleteAddressView.as_view(), name='delete_address'),
    path('addresses/set-default/<int:address_id>/', views.SetDefaultAddressView.as_view(), name='set_default_address'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),

]

