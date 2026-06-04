from django import forms
from django.core.exceptions import ValidationError
from .models import *
from django.contrib.auth.password_validation import validate_password


class UserForm(forms.ModelForm):
    # password_confirm = forms.CharField(
    #     widget=forms.PasswordInput(),
    #     label="Confirm Password"
    # )

    # password = forms.CharField(
    #     widget=forms.PasswordInput(),
    #     label="Password",
    #     min_length=6,
    #     help_text="رمز باید حداقل 6 کاراکتر باشد."
    # )

    # phone = forms.CharField(
    #     required=False,
    #     validators=[
    #         RegexValidator(
    #             regex=r'^09\d{9}$',
    #             message="شماره موبایل نامعتبر است. مثال: 09123456789"
    #         )
    #     ]
    # )

    class Meta:
        model = User
        fields = ['username', 'phone', 'email']

    def clean_username(self):
        username = self.cleaned_data['username']
        if len(username) < 3:
            raise ValidationError("نام کاربری باید حداقل 3 کاراکتر باشد.")
        if not username.isalnum():
            raise ValidationError("نام کاربری باید فقط شامل حروف و اعداد باشد.")
        if User.objects.filter(username=username).exists():
            raise ValidationError("این نام کاربری قبلاً ثبت شده است.")
        return username

    # def clean_email(self):
    #     email = self.cleaned_data['email']
    #     if User.objects.filter(email=email).exists():
    #         raise ValidationError("این ایمیل قبلاً استفاده شده است.")
    #     return email

    # def clean(self):
    #     cleaned_data = super().clean()
    #     password = cleaned_data.get("password")
    #     password_confirm = cleaned_data.get("password_confirm")

    #     if password and password_confirm and password != password_confirm:
    #         raise ValidationError("رمز عبور و تکرار آن مطابقت ندارند.")

    #     if password:
    #         if len(password) < 6:
    #             raise ValidationError("رمز عبور باید حداقل 6 کاراکتر باشد.")
    #         if password.isdigit():
    #             raise ValidationError("رمز عبور نباید فقط عدد باشد.")
    #         if password.isalpha():
    #             raise ValidationError("رمز عبور نباید فقط حروف باشد.")

    #     return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        # user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class SignupForm(forms.ModelForm):
    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={'placeholder': 'رمز عبور'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone']  
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError("رمز عبور باید حداقل 8 کاراکتر باشد")
        return password
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('این نام کاربری قبلاً ثبت شده است')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('این ایمیل قبلاً ثبت شده است')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError('این شماره موبایل قبلاً ثبت شده است')
        return phone



    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  
        
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class AddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = ['users_total_name', 'address', 'city', 'postal_code', 'phone']

class AddressFormCheckout(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = ['users_total_name', 'address', 'city', 'postal_code', 'phone', 'is_default']

class NewOrderForm(forms.Form):
    product_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )
    
    count = forms.IntegerField(
        widget=forms.NumberInput(attrs={'min': 1, 'value': 1}),
        initial=1,
        min_value=1
    )
    
    condition = forms.ChoiceField(
        choices=[('new', 'نو'), ('used', 'کارکرده')],
        widget=forms.HiddenInput(),
        initial='new'
    )


class NewWishlistForm(forms.Form):
    product_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )
    
    count = forms.IntegerField(
        widget=forms.NumberInput(attrs={'min': 1, 'value': 1}),
        initial=1,
        min_value=1
    )
    



class ChangePasswordForm(forms.Form):
    # نام‌ها دقیقاً مطابق name attribute در HTML
    currentPassword = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input modal-input',
            'placeholder': 'رمز عبور فعلی را وارد کنید'
        }),
        label='رمز عبور فعلی'
    )
    
    newPassword = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input modal-input',
            'placeholder': 'رمز عبور جدید را وارد کنید'
        }),
        validators=[validate_password],
        label='رمز عبور جدید'
    )
    
    confirmPassword = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input modal-input',
            'placeholder': 'رمز عبور جدید را تکرار کنید'
        }),
        label='تکرار رمز عبور'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_currentPassword(self):
        current = self.cleaned_data.get('currentPassword')
        if not self.user.check_password(current):
            raise forms.ValidationError('رمز عبور فعلی اشتباه است.')
        return current

    def clean(self):
        cleaned_data = super().clean()
        new = cleaned_data.get('newPassword')
        confirm = cleaned_data.get('confirmPassword')
        
        if new and confirm and new != confirm:
            raise forms.ValidationError('رمز عبور جدید و تکرار آن مطابقت ندارند.')
        return cleaned_data