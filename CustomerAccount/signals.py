from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Cart, CartItem, Product # مدل‌های خود را ایمپورت کنید

@receiver(user_logged_in)
def merge_session_cart_to_db(sender, user, request, **kwargs):
    session_cart = request.session.get('cart', {})
    
    if not session_cart:
        return
        
    cart, _ = Cart.objects.get_or_create(user=user, status='active')
    
    for key, item_data in session_cart.items():
        try:
            product = Product.objects.get(id=item_data['product_id'])
            condition = item_data['condition']
            quantity = item_data['quantity']
            
            available_stock = product.stock_new if condition == 'new' else product.stock_used
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                condition=condition,
                defaults={'quantity': 0}
            )
            
            # جمع کردن آیتم‌های سشن با آیتم‌هایی که از قبل در دیتابیس داشته
            new_qty = cart_item.quantity + quantity
            
            # در صورتی که بیشتر از موجودی بود، روی حداکثر موجودی تنظیم کن
            cart_item.quantity = min(new_qty, available_stock)
            cart_item.save()
            
        except Product.DoesNotExist:
            continue
            
    # پاک کردن سبد خرید از سشن پس از انتقال موفق به دیتابیس
    del request.session['cart']
    request.session.modified = True
