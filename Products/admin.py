from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import Product, ProductMedia, Genre, ProductAboutFeature


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1
    fields = ['media_type', 'file', 'thumbnail', 'thumbnail_preview']
    readonly_fields = ['thumbnail_preview']
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />', obj.thumbnail.url)
        return "بدون تصویر"
    thumbnail_preview.short_description = "پیش‌نمایش"
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.media_type == 'image':
            if 'thumbnail' in form.base_fields:
                form.base_fields['thumbnail'].widget = forms.HiddenInput()
        return form


class ProductAboutFeatureInline(admin.TabularInline):
    model = ProductAboutFeature
    extra = 1
    fields = ['title', 'description', 'image', 'order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "price_new", "price_used", "stock_new", "stock_used", "get_genres"]
    list_filter = ["genres"]
    search_fields = ["name", "developer", "publisher"]
    filter_horizontal = ("genres",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductMediaInline, ProductAboutFeatureInline]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'slug', 'genres', 'cover_image', 'logo')
        }),
        ('قیمت و موجودی', {
            'fields': ('price_new', 'price_used', 'stock_new', 'stock_used', 'discount_used', 'discount_new')
        }),
        ('اطلاعات تکمیلی', {
            'fields': ('developer', 'publisher', 'release_date', 'file_size_gb')
        }),
        ('بخش About', {
            'fields': ('summary', 'about_main_image')
        }),
    )

    def get_genres(self, obj):
        return ", ".join([g.label for g in obj.genres.all()])
    get_genres.short_description = "ژانرها"


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ["key", "label"]
    search_fields = ["label", "key"]


@admin.register(ProductAboutFeature)
class ProductAboutFeatureAdmin(admin.ModelAdmin):
    list_display = ["title", "product", "order"]
    list_filter = ["product"]
    search_fields = ["title", "product__name"]
    list_editable = ["order"]
