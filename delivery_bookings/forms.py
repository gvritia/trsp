"""Фильтры и пользовательская форма бронирования курьера."""

from django import forms
from django.utils import timezone

from delivery_orders.models import Order
from homepage.models import Courier
from .models import Booking


class BookingFilterForm(forms.Form):
    status = forms.ChoiceField(
        label="Статус",
        required=False,
        choices=[("", "Все"), *Booking.Status.choices],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    date = forms.DateField(
        label="Дата",
        required=False,
        widget=forms.DateInput(
            format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}
        ),
    )
    courier = forms.ModelChoiceField(
        label="Курьер",
        required=False,
        queryset=Courier.objects.order_by("name"),
        empty_label="Все",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    order = forms.ModelChoiceField(
        label="Заказ",
        required=False,
        queryset=Order.objects.order_by("id"),
        empty_label="Все",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    sort = forms.ChoiceField(
        label="Сортировка",
        required=False,
        initial="-date",
        choices=[
            ("-date", "Сначала новые"),
            ("date", "Сначала старые"),
            ("-id", "ID по убыванию"),
            ("id", "ID по возрастанию"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ("order", "courier", "delivery_date")
        widgets = {
            "order": forms.Select(attrs={"class": "form-select"}),
            "courier": forms.Select(attrs={"class": "form-select"}),
            "delivery_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "form-control"},
            ),
        }
        error_messages = {
            "order": {"required": "Выберите заказ."},
            "courier": {"required": "Выберите курьера."},
            "delivery_date": {
                "required": "Укажите дату доставки.",
                "invalid": "Укажите корректную дату доставки.",
            },
        }

    def clean_delivery_date(self):
        day = self.cleaned_data["delivery_date"]
        old_day = self.instance.delivery_date if self.instance.pk else None
        if day < timezone.localdate() and day != old_day:
            raise forms.ValidationError(
                "Нельзя бронировать курьера на прошедшую дату."
            )
        return day

    def clean(self):
        cleaned = super().clean()
        order = cleaned.get("order")
        courier = cleaned.get("courier")
        day = cleaned.get("delivery_date")
        is_active = (
            not self.instance.pk
            or self.instance.status == Booking.Status.ACTIVE
        )
        if not is_active:
            return cleaned
        if order:
            if order.status != Order.STATUS_CREATED:
                self.add_error(
                    "order", "Бронировать можно только созданный заказ."
                )
            elif (
                Booking.objects.active()
                .filter(order=order)
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                self.add_error(
                    "order", "Заказ уже имеет действующее бронирование."
                )
        if courier:
            if not courier.active:
                self.add_error("courier", "Выберите активного курьера.")
            elif order and courier.capacity < order.weight:
                self.add_error(
                    "courier", "Курьер не подходит по грузоподъёмности."
                )
            elif (
                day
                and Booking.objects.active()
                .for_date(day)
                .filter(courier=courier)
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                self.add_error("courier", "Курьер уже занят на эту дату.")
        return cleaned
