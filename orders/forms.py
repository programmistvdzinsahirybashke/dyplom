import re

from django import forms
from django.db.models import TimeField
from orders.models import Order, OrderItem, Status



class CreateOrderForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    phone_number = forms.CharField()
    requires_delivery = forms.ChoiceField(
        choices=[
            ("0", 'False'),
            ("1", 'True'),
        ],
    )
    delivery_address = forms.CharField(required=False)
    delivery_date = forms.DateField(required=False)
    delivery_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    payment_on_get = forms.ChoiceField(
        choices=[
             ("0", 'False'),
             ("1", 'True'),
             ],
    )
    comment = forms.CharField(required=False)

    def clean_phone_number(self):
        data = self.cleaned_data['phone_number']

        if not data.isdigit():
            raise forms.ValidationError("Номер телефона должен содержать только цифры")

        pattern = re.compile(r'^\d{11}$')
        if not pattern.match(data):
            raise forms.ValidationError("Неверный формат номера")

        return data
