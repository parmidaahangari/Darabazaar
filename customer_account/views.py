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
            user = User()
            user.username = form.cleaned_data['username']
            user.phone = form.cleaned_data['phone']
            user.email = form.cleaned_data['email']

            user.set_password(form.cleaned_data['password'])  
            user.save()
            return redirect("/dashboard/")



        return render(request,'customer_account/CustomerInfo.html',{
            "form": UserForm(),

            "success": True
        })