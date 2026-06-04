from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def send_order_confirmation_email(self, order_id):
    from .models import Order
    order = Order.objects.select_related('user').prefetch_related('orderdetail_set__product').get(pk=order_id)
    print(f"[TASK] ایمیل تأیید سفارش #{order.id} به {order.user.email} ارسال می‌شد")

    items = order.orderdetail_set.all()
    items_text = "\n".join(f"- {i.product.name} × {i.count} — {i.price:,} تومان" for i in items)
    
    send_mail(
        subject=f"تأیید سفارش #{order.id}",
        message=f"سفارش شما ثبت شد:\n\n{items_text}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
    )


@shared_task(bind=True, max_retries=2, autoretry_for=(Exception,), retry_backoff=True)
def send_welcome_email(self, user_id):
    from .models import User
    user = User.objects.get(pk=user_id)
    send_mail(
        subject="خوش آمدید!",
        message=f"سلام {user.username}، ثبت‌نام شما موفق بود.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
