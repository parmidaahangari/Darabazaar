from django.db import models
from django.utils.text import slugify
from decimal import Decimal


def product_cover_upload_path(instance, filename):
    return f'product/{instance.slug}/{filename}'


def product_logo_upload_path(instance, filename):
    return f'product/{instance.slug}/{filename}'


def product_about_image_upload_path(instance, filename):
    return f'product/{instance.slug}/about/{filename}'


def product_media_upload_path(instance, filename):
    return f'product/{instance.product.slug}/{filename}'


def product_feature_image_upload_path(instance, filename):
    return f'product/{instance.product.slug}/features/{filename}'

def product_thumb_upload_path(instance, filename):
    return f'product/{instance.product.slug}/{filename}'


class Genre(models.Model):
    key = models.CharField(max_length=50, unique=True)  
    label = models.CharField(max_length=50)              

    def __str__(self):
        return self.label   


class Product(models.Model):
    slug = models.SlugField(unique=True, blank=True)
    name = models.CharField(max_length=100)

    genres = models.ManyToManyField(Genre, blank=True)    
    stock_new = models.PositiveIntegerField(default=0)      
    stock_used = models.PositiveIntegerField(default=0) 

    discount_used = models.PositiveIntegerField(default=0, blank=True)     
    discount_new = models.PositiveIntegerField(default=0, blank=True)      
 
    price_new = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="قیمت نو")
    price_used = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="قیمت کارکرده")          
    developer = models.CharField(max_length=100, blank=True, default='')
    publisher = models.CharField(max_length=100, blank=True, default='')
    release_date = models.IntegerField(blank=True, null=True)
    file_size_gb = models.FloatField(blank=True, null=True)
    
    # بخش About
    summary = models.TextField(blank=True, default='', verbose_name="متن کوتاه About")
    about_main_image = models.ImageField(upload_to=product_about_image_upload_path, blank=True, null=True, verbose_name="عکس اصلی About")
    
    cover_image = models.ImageField(upload_to=product_cover_upload_path, blank=True, null=True)
    logo = models.ImageField(upload_to=product_logo_upload_path, blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def discounted_price_new(self):
        """محاسبه قیمت نو با اعمال تخفیف"""
        if self.discount_new > 0 and self.price_new > 0:
            discount_amount = (self.price_new * Decimal(self.discount_new)) / Decimal(100)
            return self.price_new - discount_amount
        return self.price_new

    @property
    def discounted_price_used(self):
        """محاسبه قیمت کارکرده با اعمال تخفیف"""
        if self.discount_used > 0 and self.price_used > 0:
            discount_amount = (self.price_used * Decimal(self.discount_used)) / Decimal(100)
            return self.price_used - discount_amount
        return self.price_used
    
    @property
    def best_price_info(self):
        """پیدا کردن ارزان‌ترین گزینه (نو یا کارکرده) به همراه تمام اطلاعاتش"""
        options = []
        
        # بررسی نسخه نو
        if self.price_new and self.price_new > 0:
            disc_n = self.discount_new or 0
            final_n = self.price_new - (self.price_new * Decimal(disc_n) / Decimal(100))
            options.append({
                'old_price': self.price_new,
                'final_price': final_n,
                'discount': disc_n,
            })
            
        # بررسی نسخه کارکرده
        if self.price_used and self.price_used > 0:
            disc_u = self.discount_used or 0
            final_u = self.price_used - (self.price_used * Decimal(disc_u) / Decimal(100))
            options.append({
                'old_price': self.price_used,
                'final_price': final_u,
                'discount': disc_u,
            })
            
        if not options:
            return None
            
        # پیدا کردن گزینه‌ای که کمترین قیمت نهایی را دارد
        best_option = min(options, key=lambda x: x['final_price'])
        return best_option
    
    

class ProductAboutFeature(models.Model):
    product = models.ForeignKey(Product, related_name="about_features", on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name="عنوان ویژگی (مثلاً Explore a Land...)", null=True, blank=True)
    description = models.TextField(verbose_name="توضیحات ویژگی", null=True, blank=True)
    image = models.ImageField(upload_to=product_feature_image_upload_path, null=True, blank=True)
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش", null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} - {self.product.name}"


class ProductMedia(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )

    product = models.ForeignKey(Product, related_name="media", on_delete=models.CASCADE)
    media_type = models.CharField(
        max_length=5,
        choices=MEDIA_TYPE_CHOICES,
        null=True,
        blank=True
    )    
    file = models.FileField(upload_to=product_media_upload_path, blank=True, null=True)
    thumbnail = models.ImageField(upload_to=product_thumb_upload_path, blank=True, null=True)

    def __str__(self):
        return f"{self.get_media_type_display()} for {self.product.name}"

    def is_image(self):
        return self.media_type == 'image'

    def is_video(self):
        return self.media_type == 'video'
