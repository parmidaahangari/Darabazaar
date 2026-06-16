
from django.http import HttpResponseForbidden

ALLOWED_IPS = [

    '127.0.0.1',

    '66.79.99.116',

]

class AdminIPWhitelistMiddleware:

    def __init__(self, get_response):

        self.get_response = get_response

    def __call__(self, request):

        if request.path.startswith('/happyadminchillingqxs9g1~qxs9g1~qxs9g/'):

            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

            if x_forwarded_for:

                ip = x_forwarded_for.split(',')[0].strip()

            else:

                ip = request.META.get('REMOTE_ADDR')

            if ip not in ALLOWED_IPS:

                return HttpResponseForbidden(f'Access denied. Your IP: {ip}')

        return self.get_response(request)

