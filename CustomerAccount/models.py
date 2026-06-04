from django.db import models, transaction
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from Products.models import Product
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('Username required')

        email = models.EmailField(max_length=100, unique=True)
        extra_fields.setdefault('is_active', True)

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phone = models.CharField(max_length=15, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    wishlist = models.ManyToManyField(Product, blank=True, related_name='wishlisted_by')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return self.username


class UserAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    users_total_name = models.CharField(max_length=100, verbose_name="نام و نام خانوادگی")  
    address = models.TextField(verbose_name="آدرس")
    city = models.CharField(max_length=100, verbose_name="شهر")
    postal_code = models.CharField(max_length=20, verbose_name="کد پستی")
    phone = models.CharField(max_length=15, verbose_name="شماره تماس")
    is_default = models.BooleanField(default=False, verbose_name="آدرس پیش‌فرض")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = "آدرس کاربر"
        verbose_name_plural = "آدرس‌های کاربر"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            with transaction.atomic():
                if self.pk:
                    UserAddress.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
                else:
                    UserAddress.objects.filter(user=self.user).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        was_default = self.is_default
        super().delete(*args, **kwargs)
        
        if was_default:
            first_addr = UserAddress.objects.filter(user=self.user).first()
            if first_addr:
                first_addr.is_default = True
                first_addr.save(update_fields=['is_default'])
    
    def __str__(self):
        return f"{self.users_total_name} - {self.city}"
    
    
class Order(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pay_date = models.DateTimeField(blank=True, null=True)
    address_text = models.TextField(null=True)  

    def __str__(self):
        return self.user.get_username()
    
    @property
    def total_discount(self):
        total = 0
        for detail in self.details.all(): 
            if detail.condition == 'new':
                discount_per_item = detail.product.price_new - detail.product.discounted_price_new
            else:
                discount_per_item = detail.product.price_used - detail.product.discounted_price_used
            
            total += (discount_per_item * detail.quantity)
        return total


class OrderDetail(models.Model):
    CONDITION_CHOICES = [
        ('new', 'آکبند'),
        ('used', 'کارکرده'),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)    
    count = models.IntegerField()
    price = models.IntegerField()
    condition = models.CharField(
        max_length=20, 
        choices=CONDITION_CHOICES, 
        default='new'
    )    
    def __str__(self):
        return f"{self.product.name} - {self.get_condition_display()}"
    
    class Meta:
        unique_together = ['order', 'product', 'condition']


class Cart(models.Model):
    STATUS_CHOICES = [
        ('active', 'فعال'),          # سبد خرید فعال کاربر
        ('abandoned', 'رها شده'),    # سبد رها شده (کاربر ولش کرد)
        ('converted', 'تبدیل شده'),  # تبدیل به Order (پرداخت موفق)
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    order = models.OneToOneField('Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='cart_source')

    cart_code = models.CharField(max_length=20, unique=True, blank=True, verbose_name="کد سبد")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'سبد خرید'
        verbose_name_plural = 'سبدهای خرید'
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(status='active'),
                name='unique_active_cart_per_user'
            )
        ]
    
    def __str__(self):
        return f"سبد {self.user.username} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        if not self.cart_code:
            self.cart_code = f"CART-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    @property
    def items_count(self):
        """تعداد کل آیتم‌ها (جمع تعداد هر محصول)"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        """جمع کل سبد"""
        return sum(item.total_price for item in self.items.all())
    
    def get_active_items(self):
        """آیتم‌هایی که هنوز موجودی دارند"""
        return [item for item in self.items.all() if item.is_available()]
    
    def is_empty(self):
        return self.items.count() == 0



    def convert_to_order(self):
        if self.status != 'active':
            raise ValueError("فقط سبد فعال قابل تبدیل است")
        
        if self.is_empty():
            raise ValueError("سبد خالی است")
        
        # چک موجودی
        for item in self.items.all():
            if not item.is_available():
                raise ValueError(f"محصول {item.product.name} ناموجود است")
        
        # ساخت Order
        order = Order.objects.create(
            user=self.user,
            pay_date=None
        )
        
        # انتقال با قیمت لحظه‌ای از Product (نه unit_price ذخیره شده)
        for item in self.items.all():
            # قیمت لحظه‌ای
            current_price = item.product.price_new if item.condition == 'new' else item.product.price_used
            
            OrderDetail.objects.create(
                order=order,
                product=item.product,
                count=item.quantity,
                price=int(current_price),  # مستقیم از Product
                condition=item.condition
            )
            
            # کاهش موجودی
            if item.condition == 'new':
                item.product.stock_new -= item.quantity
            else:
                item.product.stock_used -= item.quantity
            item.product.save(update_fields=['stock_new', 'stock_used'])
        
        # آپدیت وضعیت سبد
        self.status = 'converted'
        self.order = order
        self.converted_at = timezone.now()
        self.save()
        
        return order


class CartItem(models.Model):
    CONDITION_CHOICES = [
        ('new', 'آکبند'),
        ('used', 'کارکرده'),
    ]
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='new', verbose_name="وضعیت")
    
    # تعداد
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="تعداد")
    
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'آیتم سبد'
        verbose_name_plural = 'آیتم‌های سبد'
        unique_together = ['cart', 'product', 'condition']  # جلوگیری از تکرار
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.product.name} ({self.get_condition_display()}) × {self.quantity}"
    
    @property
    def total_price(self):
        if self.condition == 'new':
            return self.product.price_new * self.quantity
        return self.product.price_used * self.quantity
    

    @property
    def unit_price(self):
        """قیمت واحد لحظه‌ای از دیتابیس"""
        if self.condition == 'new':
            return self.product.price_new
        return self.product.price_used

    
    def get_available_stock(self):
        """موجودی فعلی محصول برای این وضعیت"""
        if self.condition == 'new':
            return self.product.stock_new
        return self.product.stock_used
    
    def is_available(self):
        """چک کردن موجودی کافی"""
        return self.get_available_stock() >= self.quantity
    
    def is_price_changed(self):
        """آیا قیمت محصول از زمان اضافه شدن تغییر کرده؟"""
        current_price = self.product.price_new if self.condition == 'new' else self.product.price_used
        return self.unit_price != current_price
