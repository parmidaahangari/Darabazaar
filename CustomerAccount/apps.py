from django.apps import AppConfig


class CustomerAccountConfig(AppConfig):
    name = 'CustomerAccount'

    def ready(self):
        import CustomerAccount.signals