from django import forms
from .models import Member

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        # Ito yung mga fields na ipapakita natin sa form
        fields = ['member_id', 'first_name', 'last_name', 'department', 'year_level', 'section', 'team', 'status']
        
        # Ito para maganda ang itsura ng mga input boxes (gumagamit tayo ng Tailwind CSS classes)
        widgets = {
            'member_id': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'placeholder': 'ELT-001'}),
            'first_name': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'placeholder': 'Joey'}),
            'last_name': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'placeholder': 'Albano'}),
            'department': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'placeholder': 'BSIT'}),
            'year_level': forms.NumberInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'placeholder': '3'}),
            'section': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'placeholder': 'A'}),
            'team': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'status': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
        }



from .models import Contribution, Expense

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['member', 'contribution_type', 'amount', 'payment_date', 'reference_no', 'notes']
        widgets = {
            'member': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'contribution_type': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'amount': forms.NumberInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'step': '0.01', 'placeholder': '50.00'}),
            'payment_date': forms.DateInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'type': 'date'}),
            'reference_no': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'placeholder': 'Optional'}),
            'notes': forms.Textarea(attrs={'class': 'border rounded px-3 py-2 w-full', 'rows': 2}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'description', 'amount', 'expense_date', 'receipt_no']
        widgets = {
            'category': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'description': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'placeholder': 'e.g., Printing of IDs'}),
            'amount': forms.NumberInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'step': '0.01', 'placeholder': '500.00'}),
            'expense_date': forms.DateInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'type': 'date'}),
            'receipt_no': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'placeholder': 'Optional'}),
        }