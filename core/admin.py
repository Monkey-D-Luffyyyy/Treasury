from django.contrib import admin
from .models import Team, Member
from .models import Contribution, Expense
from .models import FundPeriod



@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('member_id', 'last_name', 'first_name', 'team', 'department', 'year_level', 'section', 'status')
    list_filter = ('team', 'department', 'year_level', 'status')
    search_fields = ('first_name', 'last_name', 'member_id')



@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('member', 'contribution_type', 'amount', 'payment_date', 'recorded_by')
    list_filter = ('contribution_type', 'payment_date')
    search_fields = ('member__first_name', 'member__last_name', 'reference_no')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'description', 'amount', 'expense_date', 'recorded_by')
    list_filter = ('category', 'expense_date')
    search_fields = ('description', 'receipt_no')



@admin.register(FundPeriod)
class FundPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount_per_member', 'start_date', 'status')
    list_filter = ('status',)