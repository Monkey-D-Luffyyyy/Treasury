from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages # Para sa success messages
from .models import Member, Team
from .forms import MemberForm # Import natin yung form na ginawa natin
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages



from .forms import ContributionForm, ExpenseForm
from .models import Contribution, Expense
from django.db.models import Sum
from .models import FundPeriod, Note


def member_list(request):
    members = Member.objects.all().select_related('team').order_by('last_name')
    
    # Filtering logic (same as before)
    team_id = request.GET.get('team')
    department = request.GET.get('department')
    year_level = request.GET.get('year_level')
    status = request.GET.get('status')
    search_query = request.GET.get('search')

    if team_id: members = members.filter(team_id=team_id)
    if department: members = members.filter(department__icontains=department)
    if year_level: members = members.filter(year_level=year_level)
    if status: members = members.filter(status=status)
    if search_query:
        members = members.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) | 
            Q(member_id__icontains=search_query)
        )
    
    teams = Team.objects.all()
    departments = Member.objects.values_list('department', flat=True).distinct().order_by('department')
    years = Member.objects.values_list('year_level', flat=True).distinct().order_by('year_level')

    context = {
        'members': members, 'teams': teams, 'departments': departments, 'years': years,
    }
    return render(request, 'core/member_list.html', context)

# --- CREATE (ADD) ---
def member_create(request):
    if request.method == 'POST': # Kapag nag-submit ng form
        form = MemberForm(request.POST)
        if form.is_valid():
            form.save() # I-save sa database
            messages.success(request, 'Member added successfully!')
            return redirect('member_list')
    else: # Kapag unang besis pa lang buksan ang page
        form = MemberForm()
    
    return render(request, 'core/member_form.html', {'form': form, 'action': 'Add'})

# --- UPDATE (EDIT) ---
def member_update(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Member updated successfully!')
            return redirect('member_list')
    else:
        form = MemberForm(instance=member) # Pre-fill the form with existing data
        
    return render(request, 'core/member_form.html', {'form': form, 'action': 'Edit', 'member': member})

# --- DELETE ---
def member_delete(request, pk):
    member = get_object_or_404(Member, pk=pk)
    member.delete() # Tanggalin sa database
    messages.success(request, 'Member deleted successfully!')
    return redirect('member_list')




def dashboard(request):
    all_teams = Team.objects.all().order_by('name')
    
    team_stats = []
    total_members = 0
    total_expected = 0
    total_collected = 0

    for team in all_teams:
        members = Member.objects.filter(team=team, status='Active')
        member_count = members.count()
        total_members += member_count
        
        # Calculate actual collected amount for this team
        collected = Contribution.objects.filter(member__team=team).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Expected: ₱50 per active member (monthly contribution)
        expected = member_count * 50
        total_expected += expected
        total_collected += collected
        
        unpaid = expected - collected

        team_stats.append({
            'team': team,
            'member_count': member_count,
            'expected': expected,
            'collected': collected,
            'unpaid': unpaid,
            'collection_rate': round((collected / expected * 100), 1) if expected > 0 else 0
        })

    # Get total expenses
    total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    current_balance = total_collected - total_expenses

    context = {
        'team_stats': team_stats,
        'total_members': total_members,
        'total_expected': total_expected,
        'total_collected': total_collected,
        'total_unpaid': total_expected - total_collected,
        'total_expenses': total_expenses,
        'current_balance': current_balance,
    }
    return render(request, 'core/dashboard.html', context)



def contribution_create(request):
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contribution recorded successfully!')
            return redirect('treasury_ledger')
    else:
        form = ContributionForm()
    
    return render(request, 'core/contribution_form.html', {'form': form, 'action': 'Record'})


def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense recorded successfully!')
            return redirect('treasury_ledger')
    else:
        form = ExpenseForm()
    
    return render(request, 'core/expense_form.html', {'form': form, 'action': 'Record'})


def treasury_ledger(request):
    # Kunin lahat ng contributions at expenses
    contributions = Contribution.objects.all().select_related('member').order_by('-payment_date')[:20]
    expenses = Expense.objects.all().order_by('-expense_date')[:20]
    
    # Calculate totals
    total_income = Contribution.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    current_balance = total_income - total_expenses
    
    context = {
        'contributions': contributions,
        'expenses': expenses,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'current_balance': current_balance,
    }
    return render(request, 'core/treasury_ledger.html', context)



def fund_collection(request):
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum

    active_fund = FundPeriod.objects.filter(status='Active').first()
    
    if not active_fund:
        return render(request, 'core/fund_collection.html', {
            'active_fund': None, 'teams': Team.objects.all().order_by('name'),
        })
    
    selected_team_id = request.GET.get('team')
    selected_team = None
    members_status = []
    
    # Date calculations for Bulletin Board
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday()) # Monday of current week
    month_start = today.replace(day=1) # 1st day of current month

    bulletin_today = []
    bulletin_week = []
    bulletin_month = []
    all_partially_paid = []  # For the sidebar
    
    partially_paid_count = 0
    paid_count = 0
    unpaid_count = 0

    all_active_members = Member.objects.filter(status='Active').select_related('team')
    fund_amount = float(active_fund.amount_per_member)

    for member in all_active_members:
        contribs = Contribution.objects.filter(member=member, fund_period=active_fund)
        total_paid = sum(float(c.amount) for c in contribs)
        remaining = fund_amount - total_paid
        is_fully_paid = remaining <= 0.01

        # 1. Member Status for the List (only if selected team matches)
        if selected_team_id is None or member.team.id == int(selected_team_id):
            members_status.append({
                'member': member, 
                'has_paid': is_fully_paid, 
                'total_paid': total_paid, 
                'remaining': remaining,
            })

        # 2. Stats Counting
        if is_fully_paid:
            paid_count += 1
        elif total_paid > 0:
            partially_paid_count += 1
            all_partially_paid.append({
                'member': member,
                'total_paid': total_paid,
                'remaining': remaining,
                'team': member.team.name
            })
        else:
            unpaid_count += 1

        # 3. Bulletin Board Logic
        # Check payments within each timeframe
        today_payment = contribs.filter(payment_date=today).aggregate(Sum('amount'))['amount__sum'] or 0
        week_payment = contribs.filter(payment_date__gte=week_start).aggregate(Sum('amount'))['amount__sum'] or 0
        month_payment = contribs.filter(payment_date__gte=month_start).aggregate(Sum('amount'))['amount__sum'] or 0

        # Due Today: If they haven't paid anything TODAY (assuming ₱10/day expectation)
        if float(today_payment) < 10 and not is_fully_paid:
            bulletin_today.append({
                'member': member, 
                'remaining': remaining,
                'paid_today': float(today_payment)
            })
        
        # Due This Week: If they haven't paid the full ₱50 this week
        if float(week_payment) < 50 and not is_fully_paid:
            bulletin_week.append({
                'member': member, 
                'remaining': remaining,
                'paid_week': float(week_payment)
            })
        
        # Due This Month: If they haven't paid the full amount this month
        if float(month_payment) < fund_amount and not is_fully_paid:
            bulletin_month.append({
                'member': member, 
                'remaining': remaining,
                'paid_month': float(month_payment)
            })

    if selected_team_id:
        selected_team = get_object_or_404(Team, pk=selected_team_id)

    total_expected = float(active_fund.total_expected)
    total_collected = float(active_fund.total_collected)
    total_outstanding = float(active_fund.outstanding)

    context = {
        'active_fund': active_fund, 
        'teams': Team.objects.all().order_by('name'),
        'selected_team': selected_team, 
        'members_status': members_status,
        'total_expected': total_expected, 
        'total_collected': total_collected,
        'total_outstanding': total_outstanding,
        'paid_count': paid_count, 
        'unpaid_count': unpaid_count, 
        'partially_paid_count': partially_paid_count,
        # Bulletin Board Data (Top 15 each)
        'bulletin_today': bulletin_today[:15],
        'bulletin_week': bulletin_week[:15],
        'bulletin_month': bulletin_month[:15],
        # Partially Paid for Sidebar (sorted by remaining, highest first)
        'all_partially_paid': sorted(all_partially_paid, key=lambda x: x['remaining'], reverse=True)[:20],
    }
    return render(request, 'core/fund_collection.html', context)


def quick_pay(request, member_id):
    """Payment with custom amount"""
    active_fund = FundPeriod.objects.filter(status='Active').first()
    
    if not active_fund:
        messages.error(request, 'No active fund period. Please create one first.')
        return redirect('fund_collection')
    
    member = get_object_or_404(Member, pk=member_id)
    
    # Calculate how much already paid
    total_paid = Contribution.objects.filter(
        member=member, 
        fund_period=active_fund
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    remaining = float(active_fund.amount_per_member) - float(total_paid)
    
    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        
        if amount <= 0:
            messages.error(request, 'Amount must be greater than 0!')
        elif amount > remaining:
            messages.warning(request, f'Amount exceeds remaining balance (₱{remaining}). Recording full remaining balance instead.')
            amount = remaining
        
        # Record the payment
        Contribution.objects.create(
            member=member,
            fund_period=active_fund,
            contribution_type='Weekly',
            amount=amount,
            payment_date=timezone.now().date(),
            recorded_by='Treasurer',
        )
        
        messages.success(request, f'✓ Recorded ₱{amount} for {member.first_name} {member.last_name}!')
        
        # Redirect back to the same team view
        return redirect(f"{reverse('fund_collection')}?team={member.team.id}")
    
    # GET request - show the payment form
    context = {
        'member': member,
        'active_fund': active_fund,
        'total_paid': total_paid,
        'remaining': remaining,
        'default_amount': min(10, remaining),  # Default to ₱10 or remaining if less
    }
    return render(request, 'core/quick_pay.html', context)


def fund_period_create(request):
    """Create a new fund period"""
    if request.method == 'POST':
        name = request.POST.get('name')
        amount = request.POST.get('amount_per_member', 50)
        
        # Auto-close previous active fund periods
        FundPeriod.objects.filter(status='Active').update(status='Completed')
        
        # Create new one
        FundPeriod.objects.create(
            name=name,
            amount_per_member=amount,
            status='Active'
        )
        messages.success(request, f'New fund period "{name}" created!')
        return redirect('fund_collection')
    
    return render(request, 'core/fund_period_create.html')



def notes_list(request):
    notes = Note.objects.all().order_by('-due_date', '-created_at')
    return render(request, 'core/notes.html', {'notes': notes})

def note_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        due_date = request.POST.get('due_date')
        
        if title:
            Note.objects.create(title=title, content=content, due_date=due_date)
            messages.success(request, 'Note/Reminder added successfully!')
            return redirect('notes_list')
    return redirect('notes_list')

def note_toggle_complete(request, pk):
    note = get_object_or_404(Note, pk=pk)
    note.is_completed = not note.is_completed
    note.save()
    return redirect('notes_list')

def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk)
    note.delete()
    messages.success(request, 'Note deleted.')
    return redirect('notes_list')

def landing(request):
    return render(request, 'core/landing.html')

def export_collection_status(request):
    """Export collection status showing who paid, how much, and remaining"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from django.http import HttpResponse
    from django.utils import timezone
    from datetime import timedelta
    
    active_fund = FundPeriod.objects.filter(status='Active').first()
    
    if not active_fund:
        messages.error(request, 'No active fund period found.')
        return redirect('fund_collection')
    
    # Get filter parameter
    filter_type = request.GET.get('filter', 'all')  # all, week, month
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=ELITE_Collection_Status_{today}.xlsx'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Collection Status"
    
    # Headers with styling
    headers = ['Member ID', 'Last Name', 'First Name', 'Team', 'Department', 
               'Expected', 'Total Paid', 'Remaining', 'Status', 'Last Payment Date']
    
    header_fill = PatternFill(start_color='1e293b', end_color='1e293b', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # Get all active members
    members = Member.objects.filter(status='Active').select_related('team').order_by('team__name', 'last_name')
    
    row_num = 2
    fund_amount = float(active_fund.amount_per_member)
    
    for member in members:
        # Filter contributions based on selected timeframe
        contribs = Contribution.objects.filter(member=member, fund_period=active_fund)
        
        if filter_type == 'week':
            contribs = contribs.filter(payment_date__gte=week_start)
        elif filter_type == 'month':
            contribs = contribs.filter(payment_date__gte=month_start)
        
        total_paid = sum(float(c.amount) for c in contribs)
        remaining = fund_amount - total_paid
        is_fully_paid = remaining <= 0.01
        
        # Get last payment date
        last_payment = contribs.order_by('-payment_date').first()
        last_payment_date = last_payment.payment_date if last_payment else ''
        
        # Determine status
        if is_fully_paid:
            status = 'PAID'
            status_fill = PatternFill(start_color='86efac', end_color='86efac', fill_type='solid')  # Green
        elif total_paid > 0:
            status = 'PARTIAL'
            status_fill = PatternFill(start_color='fde047', end_color='fde047', fill_type='solid')  # Yellow
        else:
            status = 'UNPAID'
            status_fill = PatternFill(start_color='fca5a5', end_color='fca5a5', fill_type='solid')  # Red
        
        # Write row
        ws.cell(row=row_num, column=1, value=member.member_id)
        ws.cell(row=row_num, column=2, value=member.last_name)
        ws.cell(row=row_num, column=3, value=member.first_name)
        ws.cell(row=row_num, column=4, value=member.team.name)
        ws.cell(row=row_num, column=5, value=member.department)
        ws.cell(row=row_num, column=6, value=fund_amount)
        ws.cell(row=row_num, column=7, value=round(total_paid, 2))
        ws.cell(row=row_num, column=8, value=round(remaining, 2))
        
        status_cell = ws.cell(row=row_num, column=9, value=status)
        status_cell.fill = status_fill
        status_cell.font = Font(bold=True)
        
        ws.cell(row=row_num, column=10, value=last_payment_date)
        
        row_num += 1
    
    # Adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 30)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    wb.save(response)
    return response