from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .models import User


class UserForm(forms.ModelForm):
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(),
        label="Confirm Password"
    )

    password = forms.CharField(
        widget=forms.PasswordInput(),
        label="Password",
        min_length=6,
        help_text="رمز باید حداقل 6 کاراکتر باشد."
    )

    phone = forms.CharField(
        required=False,
        validators=[
            RegexValidator(
                regex=r'^09\d{9}$',
                message="شماره موبایل نامعتبر است. مثال: 09123456789"
            )
        ]
    )

    class Meta:
        model = User
        fields = "__all__"

    def clean_username(self):
        username = self.cleaned_data['username']
        if len(username) < 3:
            raise ValidationError("نام کاربری باید حداقل 3 کاراکتر باشد.")
        if not username.isalnum():
            raise ValidationError("نام کاربری باید فقط شامل حروف و اعداد باشد.")
        if User.objects.filter(username=username).exists():
            raise ValidationError("این نام کاربری قبلاً ثبت شده است.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("این ایمیل قبلاً استفاده شده است.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise ValidationError("رمز عبور و تکرار آن مطابقت ندارند.")

        if password:
            if len(password) < 6:
                raise ValidationError("رمز عبور باید حداقل 6 کاراکتر باشد.")
            if password.isdigit():
                raise ValidationError("رمز عبور نباید فقط عدد باشد.")
            if password.isalpha():
                raise ValidationError("رمز عبور نباید فقط حروف باشد.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
