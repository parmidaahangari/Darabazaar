import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class BluPalError(Exception):
    def __init__(self, message, error_code=None, status_code=None):
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code


class BluPalClient:
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or settings.BLUPAL_API_KEY
        self.base_url = (base_url or settings.BLUPAL_BASE_URL).rstrip('/')

        if not self.api_key:
            raise BluPalError('کلید API بلوپال تنظیم نشده است', error_code='missing_api_key')

    def _headers(self):
        return {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
        }

    def _request(self, method, path, json_data=None):
        url = f'{self.base_url}{path}'
        try:
            response = httpx.request(
                method,
                url,
                headers=self._headers(),
                json=json_data,
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            logger.exception('BluPal request failed: %s', exc)
            raise BluPalError('خطا در ارتباط با درگاه پرداخت') from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise BluPalError('پاسخ نامعتبر از درگاه پرداخت', status_code=response.status_code) from exc

        if not response.is_success or not data.get('success'):
            error_code = data.get('error', 'unknown_error')
            message = data.get('message') or self._error_message(error_code)
            raise BluPalError(message, error_code=error_code, status_code=response.status_code)

        return data

    @staticmethod
    def _error_message(error_code):
        messages = {
            'unauthorized': 'کلید API نامعتبر است',
            'amount_required': 'مبلغ ارسال نشده است',
            'amount_too_low': 'مبلغ باید حداقل ۱۰,۰۰۰ تومان باشد',
            'no_active_card': 'کارت فعالی در درگاه یافت نشد',
            'invalid_invoice_id': 'شناسه فاکتور نامعتبر است',
            'not_found': 'فاکتور یافت نشد',
            'mode_mismatch': 'عدم تطابق محیط آزمایشی و واقعی',
        }
        return messages.get(error_code, 'خطا در درگاه پرداخت')

    def create_invoice(self, amount_rial, card_number=None):
        payload = {'amount': int(amount_rial)}
        if card_number:
            payload['card_number'] = card_number
        return self._request('POST', '/v1/invoices/create', payload)

    def get_invoice(self, invoice_id):
        return self._request('GET', f'/v1/invoices/{invoice_id}')

    def simulate_payment(self, invoice_id, scenario='success'):
        return self._request(
            'POST',
            f'/v1/sandbox/invoices/{invoice_id}/simulate',
            {'scenario': scenario},
        )
