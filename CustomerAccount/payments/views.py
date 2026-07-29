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
        address_id = request.POST.get('address_id')
        if not address_id:
            messages.error(request, 'لطفاً یک آدرس انتخاب کنید')
            return redirect('addresse')

        try:
            payment = initiate_blupal_payment(request.user, address_id)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('addresse')
        except BluPalError as exc:
            messages.error(request, str(exc))
            return redirect('addresse')

        if not payment.payment_link:
            messages.error(request, 'لینک پرداخت دریافت نشد')
            return redirect('addresse')

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
