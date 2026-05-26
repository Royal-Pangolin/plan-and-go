from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Expense, Stop, Trip


SPANISH_DATE_FORMAT = "%d/%m/%Y"
DATE_INPUT_FORMATS = [SPANISH_DATE_FORMAT, "%Y-%m-%d"]
DATE_INPUT = forms.DateInput(
    format=SPANISH_DATE_FORMAT,
    attrs={
        "autocomplete": "off",
        "inputmode": "numeric",
        "pattern": r"\d{2}/\d{2}/\d{4}",
        "placeholder": "dd/mm/aaaa",
    },
)


def configure_date_fields(form, field_names):
    for field_name in field_names:
        if field_name in form.fields:
            form.fields[field_name].input_formats = DATE_INPUT_FORMATS


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label="Email", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ("name", "description", "start_date", "end_date")
        widgets = {
            "start_date": DATE_INPUT,
            "end_date": DATE_INPUT,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configure_date_fields(self, ("start_date", "end_date"))


class StopForm(forms.ModelForm):
    class Meta:
        model = Stop
        fields = (
            "name",
            "description",
            "latitude",
            "longitude",
            "start_date",
            "end_date",
            "order",
            "notes",
        )
        widgets = {
            "start_date": DATE_INPUT,
            "end_date": DATE_INPUT,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configure_date_fields(self, ("start_date", "end_date"))


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ("description", "amount", "date", "paid_by")
        widgets = {
            "date": DATE_INPUT,
        }

    def __init__(self, *args, stop, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop = stop
        configure_date_fields(self, ("date",))
        self.fields["paid_by"].queryset = stop.trip.travelers.order_by("username")
        self.fields["paid_by"].label_from_instance = lambda user: user.get_username()

    def save(self, commit=True):
        expense = super().save(commit=False)
        expense.stop = self.stop
        if commit:
            expense.save()
        return expense


class TravelerInviteForm(forms.Form):
    identifier = forms.CharField(
        label="Usuario o email",
        max_length=254,
        help_text="Debe ser una cuenta ya registrada en Plan&Go.",
    )

    def __init__(self, *args, trip, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip
        self.user = None

    def clean_identifier(self):
        identifier = self.cleaned_data["identifier"].strip()
        user = (
            User.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier))
            .order_by("id")
            .first()
        )
        if user is None:
            raise forms.ValidationError("No existe ningun usuario registrado con ese dato.")
        if self.trip.travelers.filter(pk=user.pk).exists():
            raise forms.ValidationError("Ese usuario ya forma parte del viaje.")
        self.user = user
        return identifier
