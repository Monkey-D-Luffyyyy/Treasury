from django.db import models
from django.utils import timezone
from django.db.models import Sum




class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Member(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    # Basic Info
    member_id = models.CharField(max_length=20, unique=True) # e.g., ELT-001
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # Academic Info
    department = models.CharField(max_length=100)
    year_level = models.IntegerField()
    section = models.CharField(max_length=10)
    
    # Organization Info
    team = models.ForeignKey(Team, on_delete=models.PROTECT) # Protect prevents deleting a team if it has members
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    
    # Timestamps (Good for audit trail later)
    date_joined = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.member_id})"







class Expense(models.Model):
    EXPENSE_CATEGORIES = [
        ('Event', 'Event Expenses'),
        ('Food', 'Food & Refreshments'),
        ('Transportation', 'Transportation'),
        ('Materials', 'Materials & Supplies'),
        ('Printing', 'Printing & Photocopy'),
        ('Equipment', 'Equipment'),
        ('Other', 'Other Expenses'),
    ]
    
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField(default=timezone.now)
    receipt_no = models.CharField(max_length=50, blank=True)
    recorded_by = models.CharField(max_length=100, default='Treasurer')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.category} - ₱{self.amount} ({self.description})"



class FundPeriod(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Completed', 'Completed'),
    ]
    
    name = models.CharField(max_length=100)  # e.g., "September Week 1"
    amount_per_member = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} (₱{self.amount_per_member}/member)"
    
    @property
    def total_expected(self):
        active_members = Member.objects.filter(status='Active').count()
        return active_members * self.amount_per_member
    
    @property
    def total_collected(self):
        return self.contributions.aggregate(Sum('amount'))['amount__sum'] or 0
    
    @property
    def outstanding(self):
        return self.total_expected - self.total_collected



class Contribution(models.Model):
    CONTRIBUTION_TYPES = [
        ('Monthly', 'Monthly Contribution'),
        ('Registration', 'Registration Fee'),
        ('Event', 'Event Fee'),
        ('Donation', 'Donation'),
        ('Other', 'Other Income'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='contributions')
    fund_period = models.ForeignKey(FundPeriod, on_delete=models.CASCADE, related_name='contributions', null=True, blank=True)
    contribution_type = models.CharField(max_length=20, choices=CONTRIBUTION_TYPES, default='Monthly')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    reference_no = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.CharField(max_length=100, default='Treasurer')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.member.last_name} - ₱{self.amount} ({self.contribution_type})"




class Note(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True, help_text="Reminder date")
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title