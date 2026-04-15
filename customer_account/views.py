from django.shortcuts import render, redirect
from django.views import View
from .forms import *
from .models import *

class CustomerAccountView(View):
    
    def get(self, request):
        return render(request, 'customer_account/CustomerAccount.html', {          
        })
    

class CustomerAccountInfoView(View):
    
    def get(self, request):
        return render(request, 'customer_account/CustomerInfo.html', {          
        })

    def post(self, request):
        form = UserForm(request.POST)


        if form.is_valid():
            form.save()
            return redirect('/my/dashboard/')
        
        return render(request, 'customer_account/CustomerInfo.html', {"form": form})
