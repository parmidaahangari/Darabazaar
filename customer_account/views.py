from django.shortcuts import render, redirect
from django.views import View

class CustomerAccountView(View):
    
    def get(self, request):
        return render(request, 'customer_account/CustomerAccount.html', {          
        })