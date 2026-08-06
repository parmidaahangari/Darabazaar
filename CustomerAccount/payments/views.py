import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from CustomerAccount.models import Order, PaymentTransaction
from CustomerAccount.payments.blupal import BluPalError
from CustomerAccount.payments.services import (
    handle_blupal_webhook,
    initiate_blupal_payment,
    sync_payment_status,
)

logger = logging.getLogger(__name__)


class PaymentInitiateView(LoginRequiredMixin, View):
    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        address_id = request.POST.get('address_id')
        
        # ═══ گرفتن و اعتبارسنجی هزینه ارسال ═══
        shipping_method = request.POST.get('shipping_method', 'tehran_karaj')
        shipping_cost_str = request.POST.get('shipping_cost', '150000')
        
        SHIPPING_RATES = {
            'tehran_karaj': 150000,
            'city_post': 200000
        }
        
        try:
            shipping_cost = int(shipping_cost_str)
        except (ValueError, TypeError):
            shipping_cost = SHIPPING_RATES.get(shipping_method, 150000)
        
        # اطمینان از درستی مبلغ (جلوگیری از تغییر دستی کاربر)
        expected_cost = SHIPPING_RATES.get(shipping_method, 150000)
        if shipping_cost != expected_cost:
            shipping_cost = expected_cost
        
        # ذخیره در سشن برای استفاده بعد از بازگشت از درگاه
        request.session['shipping_method'] = shipping_method
        request.session['shipping_cost'] = shipping_cost
        request.session.modified = True
        
        if not address_id:
            message = 'لطفاً یک آدرس انتخاب کنید'
            if is_ajax:
                return JsonResponse({'success': False, 'message': message}, status=400)
            messages.error(request, message)
            return redirect('addresse')

        try:
            payment = initiate_blupal_payment(
                request.user, 
                address_id, 
                shipping_cost=shipping_cost
            )
        except TypeError as exc:
            # اگر تابع نسخه قدیمیه (بدون پارامتر shipping_cost)
            if 'shipping_cost' in str(exc) or 'unexpected keyword' in str(exc):
                payment = initiate_blupal_payment(request.user, address_id)
            else:
                raise
        except ValueError as exc:
            if is_ajax:
                return JsonResponse({'success': False, 'message': str(exc)}, status=400)
            messages.error(request, str(exc))
            return redirect('addresse')
        except BluPalError as exc:
            if is_ajax:
                return JsonResponse({'success': False, 'message': str(exc)}, status=400)
            messages.error(request, str(exc))
            return redirect('addresse')
        except Exception:
            logger.exception('Payment initiation failed for user=%s address=%s', request.user.id, address_id)
            message = 'خطا در شروع پرداخت. لطفاً دوباره تلاش کنید.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': message}, status=500)
            messages.error(request, message)
            return redirect('addresse')

        if not payment.payment_link:
            message = 'لینک پرداخت دریافت نشد'
            if is_ajax:
                return JsonResponse({'success': False, 'message': message}, status=400)
            messages.error(request, message)
            return redirect('addresse')

        if is_ajax:
            return JsonResponse({'success': True, 'payment_link': payment.payment_link})

        return redirect(payment.payment_link)


class PaymentReturnView(LoginRequiredMixin, View):
    def get(self, request):
        order_id = request.GET.get('order_id')
        invoice_id = request.GET.get('invoice_id')

        payment = None
        if order_id:
            payment = (
                PaymentTransaction.objects.select_related('order')
                .filter(order_id=order_id, order__user=request.user)
                .order_by('-created_at')
                .first()
            )
        elif invoice_id:
            payment = get_object_or_404(
                PaymentTransaction.objects.select_related('order'),
                invoice_id=invoice_id,
                order__user=request.user,
            )

        if not payment:
            messages.error(request, 'تراکنش پرداخت یافت نشد')
            return redirect('cart')

        if payment.status == 'PENDING':
            try:
                order = sync_payment_status(payment)
            except BluPalError as exc:
                messages.warning(request, 'وضعیت پرداخت هنوز مشخص نیست. لطفاً چند لحظه دیگر دوباره بررسی کنید.')
                order = payment.order
        else:
            order = payment.order

        try:
            order = sync_payment_status(payment)
        except BluPalError as exc:
            messages.error(request, str(exc))
            order = payment.order

        context = {
            'order': order,
            'payment': payment,
            'details': order.orderdetail_set.select_related('product').all(),
        }
        return render(request, 'customer_account/CustomerOrder.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning('Invalid BluPal webhook payload')
            return JsonResponse({'error': 'Invalid payload'}, status=400)

        logger.info('BluPal webhook received: %s', payload)

        try:
            handle_blupal_webhook(payload)
        except ValueError as exc:
            logger.warning('BluPal webhook rejected: %s', exc)
            return JsonResponse({'error': str(exc)}, status=400)
        except Exception:
            logger.exception('BluPal webhook processing failed')
            return JsonResponse({'error': 'Processing failed'}, status=500)

        return JsonResponse({'received': True})