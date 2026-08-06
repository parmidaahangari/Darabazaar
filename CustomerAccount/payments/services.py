import logging

from django.db import transaction
from django.utils import timezone

from CustomerAccount.models import Cart, Order, PaymentTransaction
from CustomerAccount.payments.blupal import BluPalClient, BluPalError
from CustomerAccount.tasks import send_order_confirmation_email

logger = logging.getLogger(__name__)

MIN_AMOUNT_RIAL = 100_000


def toman_to_rial(amount_toman):
    return int(amount_toman) * 10


def initiate_blupal_payment(user, address_id, shipping_cost=0):
    cart = (
        Cart.objects.filter(user=user, status='active')
        .prefetch_related('items__product')
        .first()
    )
    if not cart or cart.is_empty():
        raise ValueError('سبد خرید شما خالی است')

    address = user.addresses.filter(id=address_id).first()
    if not address:
        raise ValueError('آدرس انتخاب‌شده معتبر نیست')

    # ═══ محاسبه مبلغ نهایی با احتساب هزینه ارسال ═══
    products_total = int(cart.total_price)
    amount_toman = products_total + int(shipping_cost)
    amount_rial = toman_to_rial(amount_toman)
    
    if amount_rial < MIN_AMOUNT_RIAL:
        raise ValueError('حداقل مبلغ پرداخت ۱۰,۰۰۰ تومان است')

    client = BluPalClient()
    invoice_data = client.create_invoice(amount_rial)

    required_fields = ('invoice_id', 'amount')
    missing_fields = [field for field in required_fields if field not in invoice_data]
    if missing_fields:
        logger.error('BluPal create_invoice missing fields: %s response=%s', missing_fields, invoice_data)
        raise BluPalError('پاسخ نامعتبر از درگاه پرداخت')

    with transaction.atomic():
        order = cart.create_pending_order(address)
        
        # ═══ ذخیره هزینه ارسال و آپدیت total_amount ═══
        order.shipping_cost = int(shipping_cost)
        order.total_amount = amount_toman
        order.save(update_fields=['shipping_cost', 'total_amount'])
        
        payment = PaymentTransaction.objects.create(
            order=order,
            invoice_id=invoice_data['invoice_id'],
            amount=invoice_data['amount'],
            final_amount=invoice_data.get('final_amount'),
            status=invoice_data.get('status', 'PENDING'),
            payment_link=invoice_data.get('payment_link', ''),
            card_number=invoice_data.get('card_number', ''),
            mode=invoice_data.get('mode', ''),
            raw_create_response=invoice_data,
        )

    return payment


def mark_order_paid(payment, payload=None, transaction_id=None):
    if payment.status == 'PAID' and payment.order.is_paid:
        return payment.order

    with transaction.atomic():
        payment = PaymentTransaction.objects.select_for_update().get(pk=payment.pk)
        order = Order.objects.select_for_update().get(pk=payment.order_id)

        if payment.status == 'PAID' and order.is_paid:
            return order

        payment.status = 'PAID'
        payment.paid_at = timezone.now()
        if transaction_id:
            payment.transaction_id = transaction_id
        if payload:
            payment.raw_webhook_response = payload
        payment.save()

        order.status = 'paid'
        order.pay_date = timezone.now()
        order.save(update_fields=['status', 'pay_date'])

        cart = Cart.objects.filter(user=order.user, status='active').first()
        if cart:
            cart.finalize_paid_order(order)

    send_order_confirmation_email.delay(order.id)
    return order


def sync_payment_status(payment):
    client = BluPalClient()
    invoice_data = client.get_invoice(payment.invoice_id)
    status = invoice_data.get('status', payment.status)

    payment.status = status
    payment.final_amount = invoice_data.get('final_amount', payment.final_amount)
    payment.save(update_fields=['status', 'final_amount'])

    if status == 'PAID':
        return mark_order_paid(
            payment,
            payload=invoice_data,
            transaction_id=invoice_data.get('transaction_id'),
        )

    if status in {'EXPIRED', 'CANCELED'}:
        payment.order.status = status.lower()
        payment.order.save(update_fields=['status'])

    return payment.order


def handle_blupal_webhook(payload):
    if not payload or payload.get('event') != 'payment.completed':
        raise ValueError('Invalid webhook payload')

    invoice_id = payload.get('invoice_id')
    if not invoice_id:
        raise ValueError('invoice_id is required')

    payment = PaymentTransaction.objects.select_related('order').filter(invoice_id=invoice_id).first()
    if not payment:
        raise ValueError('Payment not found')

    if payload.get('status') != 'PAID':
        raise ValueError('Unsupported webhook status')

    return mark_order_paid(
        payment,
        payload=payload,
        transaction_id=payload.get('transaction_id'),
    )