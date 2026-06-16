from django.shortcuts import render, get_object_or_404
from django.views import View
from django.db.models import Q  # ADD THIS IMPORT
from .models import Genre, Product
from CustomerAccount.forms import NewOrderForm
from django.http import JsonResponse

class ProductsView(View):
    def get(self, request, genre=None):
        products = Product.objects.all()
        
        selected_genres = request.GET.getlist('genre')
        selected_prices = request.GET.getlist('price')
        keyword = request.GET.get('keyword', '').strip()
        instock = request.GET.get('instock')
        sort = request.GET.get('sort', 'newest')
        
        # فیلتر ژانر از URL (مثلاً /products/action/)
        if genre:
            products = products.filter(genres__key__iexact=genre)
        
        # فیلتر ژانر از فرم (چک‌باکس‌ها)
        elif selected_genres and 'all' not in selected_genres:
            # استفاده از Q برای OR (یعنی اگر Action یا Adventure انتخاب شد، هر دو را نشان بده)
            genre_q = Q()
            for g in selected_genres:
                genre_q |= Q(genres__key__iexact=g)
            
            if genre_q:
                products = products.filter(genre_q)
        
        # جستجو
        if keyword:
            products = products.filter(
                Q(name__icontains=keyword) | 
                Q(summary__icontains=keyword)
            )
        
        # فیلتر قیمت
        if selected_prices:
            price_q = Q()
            for price_range in selected_prices:
                if price_range == 'under10':
                    price_q |= Q(price_used__gt=0, price_used__lt=1000000000)
                elif price_range == 'under30':
                    price_q |= Q(price_used__gte=10, price_used__lt=2000000000)
                elif price_range == 'under60':
                    price_q |= Q(price_used__gte=30, price_used__lt=4000000000)
                elif price_range == 'above60':
                    price_q |= Q(price_used__gte=4000000000)
            if price_q:
                products = products.filter(price_q)
        
        # فیلتر موجودی
        if instock:
            products = products.filter(
                Q(stock_new__gt=0) | Q(stock_used__gt=0)
            )
        
        # مرتب‌سازی
        if sort == 'price-low':
            products = products.order_by('price_used')
        elif sort == 'price-high':
            products = products.order_by('-price_used')
        elif sort == 'name':
            products = products.order_by('name')
        else:
            products = products.order_by('-id')
        
        # حذف تکراری‌ها (بسیار مهم برای ManyToMany)
        products = products.distinct()
        
        context = {
            'products': products,
            'current_genre': genre.title() if genre else 'All Games',
            'selected_genres': selected_genres,
            'selected_prices': selected_prices,
            'keyword': keyword,
            'sort': sort,
            'instock': bool(instock),
        }
        
        return render(request, 'products/products.html', context)
    

class ProductView(View):
    def get(self, request, slug):

        product = get_object_or_404(Product, slug=slug)
        new_order_form = NewOrderForm(initial={'product_id': product.id})

        return render(request, 'products/product.html', {
            "product": product,
           
        })


class SearchSuggestionsView(View):
    def get(self, request):
        keyword = request.GET.get('q', '').strip()
        
        if len(keyword) < 2:
            return JsonResponse({'results': []})
        
        try:
            # جستجو در نام محصول (حداکثر ۵ نتیجه)
            products = Product.objects.filter(
                name__icontains=keyword
            )[:5]
            
            results = []
            for product in products:
                # انتخاب قیمت: اگر کارکرده موجود بود همان،否则 نوی
                if product.price_used and product.price_used > 0:
                    price = product.price_used
                else:
                    price = product.price_new
                
                # ساخت URL تصویر
                image_url = None
                if product.cover_image:
                    try:
                        image_url = product.cover_image.url
                    except:
                        pass
                
                results.append({
                    'name': product.name,
                    'slug': product.slug,
                    'image': image_url,
                    'price': str(int(price)) if price else 'نامشخص'
                })
            
            return JsonResponse({'results': results})
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)


class ProductsGenreView(View):
    def get(self, request, genre=None):
        if genre:
            # ✅ استفاده از filter (نه get)
            # توجه: genres__key (با s) چون در مدل ManyToManyField به نام genres تعریف شده
            products = Product.objects.filter(genres__key__iexact=genre)
            
            # اگر می‌خواهید وقتی محصولی نیست، 404 نشان ندهد و فقط لیست خالی باشد:
            # (این خط اختیاری است)
            if not products.exists():
                products = Product.objects.none()  # یا می‌توانید پیام مناسب نشان دهید
                
        else:
            products = Product.objects.all()
            
        return render(request, 'products/products.html', {
            'products': products,
            'genre': genre.title() if genre else 'All Games'
        })