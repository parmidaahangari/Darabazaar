from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .forms import *
from .models import *
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.http import JsonResponse
from .forms import AddressForm
from .models import *
from Products.models import Product
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.contrib import messages  
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime
from .tasks import send_welcome_email
from django.utils.decorators import method_decorator
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse


User = get_user_model() 

class CustomerAccountView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        
        user = request.user

        return render(request, 'customer_account/CustomerAccount.html', {
            'user': user
        })


class CustomerAccountInfoView(View):
    
    def get(self, request):
        user = request.user
        form = UserForm(instance=user)
        return render(request, 'customer_account/CustomerInfo.html', {'form': form})
    
    def post(self, request):
        user = request.user
        form = UserForm(request.POST, instance=user)  

        if form.is_valid():
            form.save()
            return redirect('/my/dashboard/')
        
        return render(request, 'customer_account/CustomerInfo.html', {"form": form})


class CustomerCartView(View):
    def get(self, request):
        order_list = []

        if request.user.is_authenticated:
            # -------------------------------------------------
            # منطق کاربران لاگین شده (خواندن از دیتابیس)
            # -------------------------------------------------
            carts = (
                Cart.objects.filter(user=request.user)
                .prefetch_related('items__product')
                .order_by('-id')
            )

            with transaction.atomic():
                for cart in carts:
                    items = list(cart.items.select_related('product').all())
                    valid_items = []
                    
                    for item in items:
                        available = item.product.stock_new if item.condition == 'new' else item.product.stock_used
                        
                        if item.quantity > available:
                            if available > 0:
                                item.quantity = available
                                item.save()
                                messages.warning(
                                    request,
                                    f'موجودی "{item.product.name}" به {available} عدد کاهش یافته است. تعداد در سبد اصلاح شد.',
                                    extra_tags='stock_error'
                                )
                                valid_items.append(item)
                            else:
                                item.delete()
                                messages.error(
                                    request,
                                    f'"{item.product.name}" ناموجود شده و از سبد حذف شد.',
                                    extra_tags='stock_error'
                                )
                        else:
                            valid_items.append(item)
                    
                    total = sum(item.total_price for item in valid_items)
                    
                    order_list.append({
                        'order': cart,
                        'details': valid_items,
                        'total_price': total,
                    })

        else:
            # -------------------------------------------------
            # منطق کاربران مهمان (خواندن از سشن)
            # -------------------------------------------------
            cart_session = request.session.get('cart', {})
            valid_items = []
            total = 0
            session_modified = False
            
            # استفاده از list() برای جلوگیری از خطای تغییر دیکشنری در حین حلقه
            for item_key, item_data in list(cart_session.items()):
                try:
                    product = Product.objects.get(id=item_data['product_id'])
                except Product.DoesNotExist:
                    del cart_session[item_key]
                    session_modified = True
                    continue

                condition = item_data['condition']
                quantity = item_data['quantity']
                
                available = product.stock_new if condition == 'new' else product.stock_used
                
                if quantity > available:
                    if available > 0:
                        cart_session[item_key]['quantity'] = available
                        quantity = available
                        session_modified = True
                        messages.warning(
                            request,
                            f'موجودی "{product.name}" به {available} عدد کاهش یافته است. تعداد در سبد اصلاح شد.',
                            extra_tags='stock_error'
                        )
                    else:
                        del cart_session[item_key]
                        session_modified = True
                        messages.error(
                            request,
                            f'"{product.name}" ناموجود شده و از سبد حذف شد.',
                            extra_tags='stock_error'
                        )
                        continue
                
                # محاسبه قیمت (فرض بر این است که متدهای قیمت در مدل Product وجود دارند)
                price = product.price_new if condition == 'new' else product.price_used
                item_total_price = price * quantity
                total += item_total_price
                
                # ایجاد یک دیکشنری ساختاریافته مشابه آبجکت CartItem برای ارسال به قالب
                valid_items.append({
                    'id': item_key, # برای دکمه حذف
                    'product': product,
                    'condition': condition,
                    'quantity': quantity,
                    'total_price': item_total_price,
                })
            
            if session_modified:
                request.session['cart'] = cart_session
                request.session.modified = True

            if valid_items:
                order_list.append({
                    'order': None, # کاربر مهمان آبجکت Cart در دیتابیس ندارد
                    'details': valid_items,
                    'total_price': total,
                })

        return render(request, "customer_account/CustomerCart.html", {
            'orders': order_list
        })


class SignupView(View):

    def post(self, request):
        form = SignupForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            return JsonResponse({
                'success': True,
                'message': 'ثبت نام موفقیت آمیز',
                'redirect_url': reverse('dashboard')
            })

        errors = []
        for field, field_errors in form.errors.items():
            for error in field_errors:
                errors.append(error)

        return JsonResponse({
            'success': False,
            'errors': errors
        }, status=400)
    

class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'customer_account/Register.html', {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            raw_password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=raw_password)

            if user is not None:
                login(request, user)   
                return redirect('dashboard')
            else:
                form.add_error(None, 'نام کاربری یا رمز عبور اشتباه است.')

        return render(request, 'customer_account/Register.html', {"form": form})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')
    

class AdressView(View):
    def get(self, request, address_id=None):
        if address_id:
            user_address = get_object_or_404(UserAddress, id=address_id, user=request.user)
            form = AddressForm(instance=user_address)
        else:
            user_address = UserAddress.objects.filter(user=request.user).last()
            form = AddressForm(instance=user_address) if user_address else AddressForm()
        return render(request, "customer_account/AddressCheckout.html", {'form': form})

    def post(self, request, address_id=None):
        # تشخیص درخواست AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if address_id:
            user_address = get_object_or_404(UserAddress, id=address_id, user=request.user)
            form = AddressForm(request.POST, instance=user_address)
        else:
            # حذف آدرس قبلی و ایجاد جدید
            UserAddress.objects.filter(user=request.user).delete()
            form = AddressForm(request.POST)
            
        if form.is_valid():
            add = form.save(commit=False)
            add.user = request.user
            add.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True, 
                    'message': 'آدرس با موفقیت ثبت شد',
                    'address_id': add.id
                })
            
            # برای درخواست معمولی (غیر AJAX)
            messages.success(request, 'آدرس با موفقیت ثبت شد')
            return redirect('dashboard')
            
        else:
            # اگر فرم نامعتبر است
            if is_ajax:
                errors = {field: error_list for field, error_list in form.errors.items()}
                return JsonResponse({
                    'success': False,
                    'message': 'خطا در اعتبارسنجی فرم',
                    'errors': errors
                }, status=400)
            
            print(form.errors)
            return render(request, "customer_account/AddressCheckout.html", {'form': form})


class RemoveFromCartView(View):
    def post(self, request, item_id):
        # item_id برای کاربر لاگین شده برابر با شناسه CartItem (عدد) است.
        # برای کاربر مهمان برابر با کلید سشن (مثلا "12_new") است.
        
        if request.user.is_authenticated:
            # حذف از دیتابیس
            cart_item = get_object_or_404(
                CartItem,
                id=item_id,
                cart__user=request.user,
                cart__status='active'
            )
            cart_item.delete()
        else:
            # حذف از سشن
            cart = request.session.get('cart', {})
            item_key = str(item_id)
            if item_key in cart:
                del cart[item_key]
                request.session['cart'] = cart
                request.session.modified = True
                
        return redirect('cart')


@require_POST
def add_new_cart(request):
    product_id = request.POST.get('product_id')
    condition = request.POST.get('condition', 'new')
    
    try:
        quantity = int(request.POST.get('count', 1))
        if quantity < 1:
            raise ValueError
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'تعداد نامعتبر است'}, status=400)
    
    if condition not in ['new', 'used']:
        return JsonResponse({'status': 'error', 'message': 'وضعیت نامعتبر است'}, status=400)
    
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'محصول وجود ندارد'}, status=404)
    
    available_stock = product.stock_new if condition == 'new' else product.stock_used
    
    # -----------------------------------------
    # حالت اول: کاربر لاگین کرده است (دیتابیس)
    # -----------------------------------------
    if request.user.is_authenticated:
        try:
            with transaction.atomic():
                cart, _ = Cart.objects.get_or_create(user=request.user, status='active')
                item, created = CartItem.objects.get_or_create(
                    cart=cart, product=product, condition=condition, defaults={'quantity': 0}
                )
                
                new_quantity = item.quantity + quantity
                if new_quantity > available_stock:
                    remaining = available_stock - item.quantity
                    msg = f'موجودی کافی نیست. تنها {remaining} عدد دیگر می‌توانید اضافه کنید' if remaining > 0 else f'حداکثر موجودی ({available_stock}) در سبد شماست.'
                    return JsonResponse({'status': 'error', 'message': msg}, status=400)
                
                item.quantity = new_quantity
                item.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'محصول به سبد خرید اضافه شد',
                    'cart_items_count': cart.items_count,
                    'cart_total': str(cart.total_price),
                    'item_quantity': item.quantity
                })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطای سرور: {str(e)}'}, status=500)

    # -----------------------------------------
    # حالت دوم: کاربر مهمان است (سشن)
    # -----------------------------------------
    else:
        # ساختار سشن: dictionary که کلید آن ترکیبی از آیدی محصول و وضعیت است
        cart = request.session.get('cart', {})
        item_key = f"{product_id}_{condition}"
        
        current_qty = cart.get(item_key, {}).get('quantity', 0)
        new_quantity = current_qty + quantity
        
        if new_quantity > available_stock:
            remaining = available_stock - current_qty
            msg = f'موجودی کافی نیست. تنها {remaining} عدد دیگر می‌توانید اضافه کنید' if remaining > 0 else f'حداکثر موجودی ({available_stock}) در سبد شماست.'
            return JsonResponse({'status': 'error', 'message': msg}, status=400)
        
        cart[item_key] = {
            'product_id': str(product_id),
            'condition': condition,
            'quantity': new_quantity
        }
        request.session['cart'] = cart
        request.session.modified = True
        
        # محاسبه تعداد کل برای کاربر مهمان
        cart_items_count = sum(item['quantity'] for item in cart.values())
        
        return JsonResponse({
            'status': 'success',
            'message': 'محصول به سبد خرید اضافه شد (مهمان)',
            'cart_items_count': cart_items_count,
            'cart_total': "0",  # اینجا می‌توانید تابعی بنویسید که قیمت کل سشن را حساب کند
            'item_quantity': new_quantity
        })


@login_required
def add_new_wishlist(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر است'}, status=400)

    product_id = request.POST.get('product_id')
    
    if not product_id:
        return JsonResponse({'status': 'error', 'message': 'شناسه محصول ارسال نشده است'}, status=400)

    try:
        product = Product.objects.get(id=product_id)
        request.user.wishlist.add(product)
        return JsonResponse({'status': 'success', 'message': 'محصول به علاقه‌مندی‌ها اضافه شد'})
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'محصول وجود ندارد'}, status=404)
    

class CustomerWishlistView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        
        wishlist_products = request.user.wishlist.all()
        
        return render(request, "customer_account/CustomerWishlist.html", {
            'wishlist_products': wishlist_products
        })

    
class RemoveFromWishlistView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'ابتدا وارد شوید'})

        product_id = request.POST.get('product_id')
        
        try:
            product = Product.objects.get(id=product_id)
            request.user.wishlist.remove(product)
            return JsonResponse({'success': True, 'message': 'از علاقه‌مندی‌ها حذف شد'})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'محصول یافت نشد'})


class CustomerOrderView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        orders = (
            Order.objects.filter(user=request.user)
            .prefetch_related('orderdetail_set__product')
            .order_by('-id')
        )

        order_list = []
        for order in orders:
            details = order.orderdetail_set.all()
            total = sum(item.price * item.count for item in details)

            order_list.append({
                'order': order,
                'details': details,
                'total_price': total,
            })

        return render(request, "customer_account/CustomerOrder.html", {
            'orders': order_list
        })


class UpdateCartItemQuantityView(View):
    def post(self, request, item_id):
        try:
            # خواندن مقدار تغییر از درخواست
            data = json.loads(request.body)
            change = int(data.get('change', 0))
        except (ValueError, TypeError, json.JSONDecodeError):
            return JsonResponse({'success': False, 'error': 'اطلاعات نامعتبر است'}, status=400)

        # -------------------------------------------------
        # کاربر لاگین شده (دیتابیس)
        # -------------------------------------------------
        if request.user.is_authenticated:
            try:
                cart_item = get_object_or_404(
                    CartItem,
                    id=item_id,
                    cart__user=request.user,
                    cart__status='active'
                )
                
                new_quantity = cart_item.quantity + change
                
                # اگر تعداد به ۰ یا کمتر رسید، آیتم حذف شود
                if new_quantity <= 0:
                    cart = cart_item.cart
                    cart_item.delete()
                    return JsonResponse({
                        'success': True,
                        'deleted': True,
                        'items_count': cart.items_count, # فرض بر این است که پراپرتی/متد است
                        'cart_total': float(cart.total_price),
                        'message': 'محصول از سبد حذف شد'
                    })
                
                # چک کردن موجودی انبار برای افزایش تعداد
                if change > 0:
                    available_stock = cart_item.get_available_stock() # فرض بر وجود این متد در مدل
                    if new_quantity > available_stock:
                        return JsonResponse({
                            'success': False,
                            'error': f'موجودی کافی نیست. حداکثر: {available_stock} عدد'
                        }, status=400)
                
                # ذخیره تعداد جدید
                cart_item.quantity = new_quantity
                cart_item.save()
                cart = cart_item.cart
                
                return JsonResponse({
                    'success': True,
                    'quantity': new_quantity,
                    'item_total': float(cart_item.total_price),
                    'cart_total': float(cart.total_price),
                    'items_count': cart.items_count
                })
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)

        # -------------------------------------------------
        # کاربر مهمان (سشن)
        # -------------------------------------------------
        else:
            cart_session = request.session.get('cart', {})
            item_key = str(item_id)
            
            if item_key not in cart_session:
                return JsonResponse({'success': False, 'error': 'آیتم در سبد خرید یافت نشد'}, status=404)
            
            item_data = cart_session[item_key]
            new_quantity = item_data['quantity'] + change
            
            try:
                # ایمپورت مدل Product در بالای فایل فراموش نشود
                from .models import Product 
                product = Product.objects.get(id=item_data['product_id'])
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'محصول یافت نشد'}, status=404)

            # محاسبه تعداد و جمع کل سبد مهمان
            def get_session_totals():
                total_price = 0
                items_count = len(cart_session) # یا sum(v['quantity'] for v in cart_session.values()) بسته به نیاز شما
                for k, v in cart_session.items():
                    try:
                        p = Product.objects.get(id=v['product_id'])
                        price = p.price_new if v['condition'] == 'new' else p.price_used
                        total_price += price * v['quantity']
                    except Product.DoesNotExist:
                        continue
                return total_price, items_count

            # اگر تعداد به ۰ یا کمتر رسید، حذف شود
            if new_quantity <= 0:
                del cart_session[item_key]
                request.session['cart'] = cart_session
                request.session.modified = True
                
                cart_total, items_count = get_session_totals()
                
                return JsonResponse({
                    'success': True,
                    'deleted': True,
                    'items_count': items_count,
                    'cart_total': float(cart_total),
                    'message': 'محصول از سبد حذف شد'
                })

            # چک کردن موجودی انبار برای افزایش
            if change > 0:
                available_stock = product.stock_new if item_data['condition'] == 'new' else product.stock_used
                if new_quantity > available_stock:
                    return JsonResponse({
                        'success': False,
                        'error': f'موجودی کافی نیست. حداکثر: {available_stock} عدد'
                    }, status=400)

            # اعمال تغییرات و ذخیره سشن
            cart_session[item_key]['quantity'] = new_quantity
            request.session['cart'] = cart_session
            request.session.modified = True

            # محاسبه قیمت‌ها برای رسپانس
            price = product.price_new if item_data['condition'] == 'new' else product.price_used
            item_total = price * new_quantity
            cart_total, items_count = get_session_totals()

            return JsonResponse({
                'success': True,
                'quantity': new_quantity,
                'item_total': float(item_total),
                'cart_total': float(cart_total),
                'items_count': items_count
            })

MAX_ADDRESSES = 10

class CustomerAdressesView(View):
    def get(self, request, address_id=None):
        # گرفتن همه آدرس‌های کاربر
        addresses = UserAddress.objects.filter(user=request.user)
        address_count = addresses.count()
        
        # اگر address_id داده شده، آن را برای ویرایش لود کن
        if address_id:
            address_instance = get_object_or_404(UserAddress, id=address_id, user=request.user)
            form = AddressForm(instance=address_instance)
            edit_mode = True
        else:
            address_instance = None
            form = AddressForm()
            edit_mode = False
            
        context = {
            'addresses': addresses,
            'form': form,
            'edit_mode': edit_mode,
            'address_id': address_id,
            'address_count': address_count,
            'can_add_more': address_count < MAX_ADDRESSES,
            'max_addresses': MAX_ADDRESSES
        }
        return render(request, "customer_account/CustomerAddress.html", context)

    def post(self, request, address_id=None):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # بررسی محدودیت تعداد آدرس‌ها در صورت ایجاد جدید
        if not address_id:
            current_count = UserAddress.objects.filter(user=request.user).count()
            if current_count >= MAX_ADDRESSES:
                msg = f'شما حداکثر می‌توانید {MAX_ADDRESSES} آدرس داشته باشید'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': msg}, status=400)
                messages.error(request, msg)
                return redirect('customer_addresses')
        
        if address_id:
            # ویرایش آدرس موجود
            address_instance = get_object_or_404(UserAddress, id=address_id, user=request.user)
            form = AddressForm(request.POST, instance=address_instance)
        else:
            # ایجاد آدرس جدید
            form = AddressForm(request.POST)
            
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # اگر اولین آدرس است، آن را پیش‌فرض کن
            if not UserAddress.objects.filter(user=request.user).exists():
                address.is_default = True
                
            address.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True, 
                    'message': 'آدرس با موفقیت ذخیره شد',
                    'address_id': address.id,
                    'is_default': address.is_default
                })
            
            messages.success(request, 'آدرس با موفقیت ذخیره شد')
            return redirect('customer_addresses')
            
        else:
            if is_ajax:
                errors = {field: error_list for field, error_list in form.errors.items()}
                return JsonResponse({
                    'success': False,
                    'message': 'خطا در اعتبارسنجی فرم',
                    'errors': errors
                }, status=400)
            
            # در صورت خطا، صفحه را با فرم خطادار رندر کن
            addresses = UserAddress.objects.filter(user=request.user)
            return render(request, "customer_account/CustomerAddress.html", {
                'form': form,
                'addresses': addresses,
                'edit_mode': bool(address_id),
                'address_id': address_id
            })


class DeleteAddressView(View):
    def post(self, request, address_id):
        address = get_object_or_404(UserAddress, id=address_id, user=request.user)
        
        # اگر آدرس حذف شده default بود، آدرس دیگری را default کن
        was_default = address.is_default
        address.delete()
        
        if was_default:
            # اولین آدرس باقیمانده را default کن
            first_address = UserAddress.objects.filter(user=request.user).first()
            if first_address:
                first_address.is_default = True
                first_address.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'آدرس حذف شد'})
        
        messages.success(request, 'آدرس با موفقیت حذف شد')
        return redirect('customer_addresses')


class SetDefaultAddressView(View):
    def post(self, request, address_id):
        address = get_object_or_404(UserAddress, id=address_id, user=request.user)
        
        with transaction.atomic():
            UserAddress.objects.filter(user=request.user).update(is_default= False)
            address.is_default = True
            address.save()

        return JsonResponse({'success': True, 'message': 'آدرس پیش‌فرض تنظیم شد'})        


class CustomerAdressesViewCheckout(LoginRequiredMixin, View):
    def get_cart(self, user):
        """گرفتن سبد خرید فعال کاربر"""
        return Cart.objects.filter(
            user=user, 
            status='active'
        ).prefetch_related('items__product').first()
    
    def get_context(self, request, form=None, edit_mode=False, address_id=None):
        """کنتکست مشترک برای get و post"""
        addresses = UserAddress.objects.filter(user=request.user)
        cart = self.get_cart(request.user)
        
        # محاسبه تخفیف (اگر سیستم تخفیف دارید)
        discount = 0
        total_price = cart.total_price if cart else 0
        final_price = total_price - discount
        
        context = {
            'addresses': addresses,
            'address_count': addresses.count(),
            'can_add_more': addresses.count() < MAX_ADDRESSES,
            'max_addresses': MAX_ADDRESSES,
            'cart': cart,  # اضافه کردن کارت
            'discount': discount,
            'final_price': final_price,
        }
        
        if form:
            context['form'] = form
        else:
            context['form'] = AddressFormCheckout()
            
        if edit_mode:
            context['edit_mode'] = True
            context['address_id'] = address_id
            
        return context

    def get(self, request, address_id=None):
        # اگر address_id داده شده، فرم ویرایش رو لود کن
        if address_id:
            address_instance = get_object_or_404(
                UserAddress, 
                id=address_id, 
                user=request.user
            )
            form = AddressFormCheckout(instance=address_instance)
            return render(
                request, 
                "customer_account/AddressCheckout.html", 
                self.get_context(request, form, edit_mode=True, address_id=address_id)
            )
        
        return render(
            request, 
            "customer_account/AddressCheckout.html", 
            self.get_context(request)
        )

    def post(self, request, address_id=None):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # تشخیص ویرایش vs ایجاد جدید
        if address_id:
            # ویرایش آدرس موجود
            address_instance = get_object_or_404(
                UserAddress, 
                id=address_id, 
                user=request.user
            )
            form = AddressFormCheckout(request.POST, instance=address_instance)
            success_message = 'آدرس با موفقیت ویرایش شد'
        else:
            # ایجاد آدرس جدید
            # بررسی محدودیت تعداد
            current_count = UserAddress.objects.filter(user=request.user).count()
            if current_count >= MAX_ADDRESSES:
                msg = f'شما حداکثر می‌توانید {MAX_ADDRESSES} آدرس داشته باشید'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': msg}, status=400)
                messages.error(request, msg)
                return redirect('checkout_addresses')
            
            form = AddressFormCheckout(request.POST)
            success_message = 'آدرس با موفقیت ثبت شد'
            
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # اگر اولین آدرس کاربر است یا is_default تیک خورده
            is_default = request.POST.get('is_default') == 'on' or \
                        request.POST.get('is_default') == 'true'
            
            if not UserAddress.objects.filter(user=request.user).exists():
                address.is_default = True
            else:
                address.is_default = is_default
            
            # ذخیره
            address.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True, 
                    'message': success_message,
                    'address_id': address.id,
                    'is_default': address.is_default,
                    'data': {
                        'name': address.users_total_name,
                        'address': address.address,
                        'city': address.city,
                        'postal': address.postal_code,
                        'phone': address.phone,
                    }
                })
            
            messages.success(request, success_message)
            return redirect('checkout_addresses')
            
        else:
            # خطا در اعتبارسنجی
            if is_ajax:
                errors = {
                    field: [str(error) for error in error_list] 
                    for field, error_list in form.errors.items()
                }
                return JsonResponse({
                    'success': False,
                    'message': 'خطا در اعتبارسنجی فرم',
                    'errors': errors
                }, status=400)
            
            # حالت غیر AJAX
            return render(
                request, 
                "customer_account/AddressCheckout.html", 
                self.get_context(request, form, bool(address_id), address_id)
            )


def register(request):
    if request.method == 'POST':
        # ساخت یوزر
        user = User.objects.create_user(
            username=request.POST['username'],
            email=request.POST['email'],
            password=request.POST['password'],
        )
        
        # ارسال فوری
        send_welcome_email.delay(user.id)
        
        # ارسال با تاخیر ۵ دقیقه‌ای
        send_welcome_email.apply_async(
            args=[user.id],
            countdown=300,
        )
        
        # ارسال در زمان مشخص
        send_welcome_email.apply_async(
            args=[user.id],
            eta=datetime(2026, 3, 1, 10, 0, 0),
        )
        
        login(request, user)
        return redirect('dashboard')
    
    return render(request, 'Register.html')


@method_decorator(login_required, name='dispatch')

class ChangePasswordView(View):
    def get(self, request):
        form = ChangePasswordForm(user=request.user)
        return render(request, 'customer_account/CustomerInfo.html', {'form': form})

    def post(self, request):
        form = ChangePasswordForm(user=request.user, data=request.POST)
        
        if form.is_valid():
            # تغییر پسورد
            request.user.set_password(form.cleaned_data['newPassword'])
            request.user.save()
            
            # جلوگیری از لاگ اوت
            update_session_auth_hash(request, request.user)
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'رمز عبور با موفقیت تغییر کرد.'})
            
            messages.success(request, 'رمز عبور با موفقیت تغییر کرد.')
            return redirect('dashboard')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = form.errors.as_json()
            # استخراج اولین پیام خطا برای نمایش ساده‌تر
            error_msg = "خطا در مقادیر وارد شده"
            for field, field_errors in form.errors.items():
                error_msg = field_errors[0]
                break
            return JsonResponse({'success': False, 'error': error_msg, 'errors': form.errors}, status=400)

        # اگر خطا بود و ایجکس نبود، فرم با خطاها رندر می‌شه
        # برای جلوگیری از خالی شدن فرم اصلی، باید اطلاعات کاربر را هم بفرستیم
        user_form = UserForm(instance=request.user)
        return render(request, 'customer_account/CustomerInfo.html', {
            'form': user_form,
            'password_form': form,
            'show_password_modal': True
        })