from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Group, Expense, UserProfile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one number.")
        if not any(char.isalpha() for char in password):
            raise ValidationError("Password must contain at least one letter.")
        return password
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            # UserProfile will be created by the signal
        return user

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class GroupCreationForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Group Name (e.g., Flat 5B)'})
        }

class JoinGroupForm(forms.Form):
    code = forms.CharField(max_length=12, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Group Code'}))
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        try:
            Group.objects.get(code=code)
        except Group.DoesNotExist:
            raise ValidationError("Invalid group code. Please check and try again.")
        return code

class ExpenseForm(forms.ModelForm):
    shared_among = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = Expense
        fields = ["title", "amount", "paid_by", "shared_among"]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'paid_by': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)
        super(ExpenseForm, self).__init__(*args, **kwargs)
        
        if group:
            self.fields['paid_by'].queryset = User.objects.filter(profile__group=group)
            self.fields['shared_among'].queryset = User.objects.filter(profile__group=group)
            
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError("Amount must be a positive number.")
        return amount 