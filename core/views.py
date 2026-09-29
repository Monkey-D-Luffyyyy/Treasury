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

    # 1. Kunin LAHAT ng Fund Periods (Active man o Completed)
    all_funds = FundPeriod.objects.all().order_by('-start_date')
    
    # 2. Alamin kung aling Fund ang pinili ng Treasurer (base sa URL ?fund=1)
    selected_fund_id = request.GET.get('fund')
    
    if selected_fund_id:
        selected_fund = get_object_or_404(FundPeriod, pk=selected_fund_id)
    else:
        # Default: Ipakita ang Active, o kung wala, ang pinakabago
        selected_fund = all_funds.filter(status='Active').first() or all_funds.first()

    if not selected_fund:
        return render(request, 'core/fund_collection.html', {
            'all_funds': all_funds, 'selected_fund': None, 'teams': Team.objects.all().order_by('name'),
        })

    selected_team_id = request.GET.get('team')
    selected_team = None
    members_status = []
    
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    bulletin_today = []
    bulletin_week = []
    bulletin_month = []
    all_partially_paid = []
    
    partially_paid_count = 0
    paid_count = 0
    unpaid_count = 0

    all_active_members = Member.objects.filter(status='Active').select_related('team')
    fund_amount = float(selected_fund.amount_per_member)

    for member in all_active_members:
        # IMPORTANT: Filter contributions ONLY for the SELECTED fund period
        contribs = Contribution.objects.filter(member=member, fund_period=selected_fund)
        total_paid = sum(float(c.amount) for c in contribs)
        remaining = fund_amount - total_paid
        is_fully_paid = remaining <= 0.01

        if selected_team_id is None or member.team.id == int(selected_team_id):
            members_status.append({
                'member': member, 'has_paid': is_fully_paid, 
                'total_paid': total_paid, 'remaining': remaining,
            })

        if is_fully_paid:
            paid_count += 1
        elif total_paid > 0:
            partially_paid_count += 1
            all_partially_paid.append({
                'member': member, 'total_paid': total_paid, 'remaining': remaining, 'team': member.team.name
            })
        else:
            unpaid_count += 1

        # Bulletin Board Logic (For the selected fund)
        if not is_fully_paid:
            paid_today = contribs.filter(payment_date=today).exists()
            paid_this_week = contribs.filter(payment_date__gte=week_start).exists()
            paid_this_month = contribs.filter(payment_date__gte=month_start).exists()

            if not paid_today: bulletin_today.append({'member': member, 'remaining': remaining})
            if not paid_this_week: bulletin_week.append({'member': member, 'remaining': remaining})
            if not paid_this_month: bulletin_month.append({'member': member, 'remaining': remaining})

    if selected_team_id:
        selected_team = get_object_or_404(Team, pk=selected_team_id)

    total_expected = float(selected_fund.total_expected)
    total_collected = float(selected_fund.total_collected)
    total_outstanding = float(selected_fund.outstanding)

    context = {
        'all_funds': all_funds,
        'selected_fund': selected_fund, 
        'teams': Team.objects.all().order_by('name'),
        'selected_team': selected_team, 
        'members_status': members_status,
        'total_expected': total_expected, 'total_collected': total_collected, 'total_outstanding': total_outstanding,
        'paid_count': paid_count, 'unpaid_count': unpaid_count, 'partially_paid_count': partially_paid_count,
        'bulletin_today': bulletin_today, 'bulletin_week': bulletin_week, 'bulletin_month': bulletin_month,
        'all_partially_paid': sorted(all_partially_paid, key=lambda x: x['remaining'], reverse=True),
    }
    return render(request, 'core/fund_collection.html', context)


def quick_pay(request, member_id, fund_id):
    """Payment for a SPECIFIC fund period"""
    selected_fund = get_object_or_404(FundPeriod, pk=fund_id)
    member = get_object_or_404(Member, pk=member_id)
    
    # Check kung nagbayad na ba siya SA SPECIFIC NA FUND NA TO
    existing = Contribution.objects.filter(member=member, fund_period=selected_fund).first()
    
    if existing:
        messages.warning(request, f'{member.last_name} already paid for {selected_fund.name}!')
    else:
        amount = float(request.POST.get('amount', selected_fund.amount_per_member))
        
        # Record the payment to the SPECIFIC fund period
        Contribution.objects.create(
            member=member,
            fund_period=selected_fund, # Dito na natin inaasign kung saang week napunta ang pera
            contribution_type='Weekly',
            amount=amount,
            payment_date=timezone.now().date(),
            recorded_by='Treasurer',
        )
        messages.success(request, f'✓ {member.first_name} {member.last_name} paid ₱{amount} for {selected_fund.name}!')
    
    return redirect(f"{reverse('fund_collection')}?fund={selected_fund.id}")

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

def weekly_tracker(request):
    from django.db.models import Sum
    
    # Get the latest 6 fund periods (Weeks)
    fund_periods = list(FundPeriod.objects.order_by('start_date')[:6])
    
    members = Member.objects.filter(status='Active').select_related('team').order_by('last_name', 'first_name')
    
    tracker_data = []
    for member in members:
        row = {
            'member': member,
            'weekly_remaining': [],
            'total_remaining': 0.0
        }
        for fp in fund_periods:
            expected = float(fp.amount_per_member)
            paid = Contribution.objects.filter(member=member, fund_period=fp).aggregate(Sum('amount'))['amount__sum'] or 0
            paid = float(paid)
            remaining = max(0.0, expected - paid)
            row['weekly_remaining'].append(remaining)
            row['total_remaining'] += remaining
            
        tracker_data.append(row)
        
    context = {
        'fund_periods': fund_periods,
        'tracker_data': tracker_data
    }
    return render(request, 'core/weekly_tracker.html', context)

def export_weekly_tracker(request):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from django.http import HttpResponse
    from django.db.models import Sum
    from django.utils import timezone
    
    fund_periods = list(FundPeriod.objects.order_by('start_date')[:6])
    members = Member.objects.filter(status='Active').select_related('team').order_by('last_name', 'first_name')
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=ELITE_Weekly_Tracker_{timezone.now().date()}.xlsx'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Weekly Fund Tracker"
    
    # Headers
    headers = ['Member ID', 'Last Name', 'First Name', 'Team', 'Department']
    for i in range(len(fund_periods)):
        headers.append(f'Week {i+1} Remaining')
    headers.append('Total Remaining')
    
    header_fill = PatternFill(start_color='1e293b', end_color='1e293b', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        
    row_num = 2
    for row_data in tracker_data_logic(members, fund_periods): # Helper logic
        ws.cell(row=row_num, column=1, value=row_data['member'].member_id)
        ws.cell(row=row_num, column=2, value=row_data['member'].last_name)
        ws.cell(row=row_num, column=3, value=row_data['member'].first_name)
        ws.cell(row=row_num, column=4, value=row_data['member'].team.name)
        ws.cell(row=row_num, column=5, value=row_data['member'].department)
        
        col_idx = 6
        for rem in row_data['weekly_remaining']:
            cell = ws.cell(row=row_num, column=col_idx, value=rem)
            if rem == 0:
                cell.fill = PatternFill(start_color='86efac', end_color='86efac', fill_type='solid') # Green
            elif rem > 0:
                cell.fill = PatternFill(start_color='fca5a5', end_color='fca5a5', fill_type='solid') # Red
            col_idx += 1
            
        total_cell = ws.cell(row=row_num, column=col_idx, value=row_data['total_remaining'])
        if row_data['total_remaining'] == 0:
            total_cell.font = Font(bold=True, color='008000')
        else:
            total_cell.font = Font(bold=True, color='FF0000')
            
        row_num += 1
        
    for column in ws.columns:
        max_length = max(len(str(cell.value)) for cell in column if cell.value is not None)
        ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 25)
        
    wb.save(response)
    return response

# Helper function to avoid code duplication
def tracker_data_logic(members, fund_periods):
    for member in members:
        row = {'member': member, 'weekly_remaining': [], 'total_remaining': 0.0}
        for fp in fund_periods:
            expected = float(fp.amount_per_member)
            paid = Contribution.objects.filter(member=member, fund_period=fp).aggregate(Sum('amount'))['amount__sum'] or 0
            remaining = max(0.0, expected - float(paid))
            row['weekly_remaining'].append(remaining)
            row['total_remaining'] += remaining
        yield row