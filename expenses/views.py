from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q, Case, When, DecimalField, Value
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, requires_csrf_token
from django.views.decorators.debug import sensitive_post_parameters
from django.middleware.csrf import get_token, rotate_token
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import UserRegistrationForm, UserLoginForm, GroupCreationForm, JoinGroupForm, ExpenseForm
from .models import Group, UserProfile, Expense

@requires_csrf_token
def register(request):
    """View for user registration with CSRF protection"""
    # Generate a fresh CSRF token
    rotate_token(request)
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Generate a fresh CSRF token after login
            rotate_token(request)
            
            messages.success(request, f"Account created for {user.username}. You are now logged in.")
            return redirect('group_setup')
        else:
            # If form is invalid, generate a new CSRF token
            rotate_token(request)
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
        'csrf_token': get_token(request)
    }
    
    return render(request, 'expenses/register.html', context)

def csrf_failure(request, reason=""):
    """Custom view for CSRF failures"""
    # Generate a new CSRF token
    rotate_token(request)
    
    # Add an error message
    messages.error(request, "Your session has expired. Please try again.")
    
    # Redirect to login page with new token
    return redirect('login')

@requires_csrf_token
def user_login(request):
    """View for user login with extra CSRF protection"""
    # Generate a fresh CSRF token
    rotate_token(request)
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                
                # Generate a fresh CSRF token after login
                rotate_token(request)
                
                # Check if user is in a group, if not, redirect to group setup
                if hasattr(user, 'profile') and user.profile.group:
                    return redirect('dashboard')
                else:
                    return redirect('group_setup')
        else:
            # If form is invalid, generate a new CSRF token
            rotate_token(request)
    else:
        form = UserLoginForm()
    
    context = {
        'form': form,
        'csrf_token': get_token(request)
    }
    
    response = render(request, 'expenses/login.html', context)
    return response

@login_required
@csrf_protect
def group_setup(request):
    # If user already has a group, redirect to dashboard
    if request.user.profile.group:
        return redirect('dashboard')
    
    # Force CSRF token creation
    get_token(request)
    
    creation_form = GroupCreationForm()
    join_form = JoinGroupForm()
    
    context = {
        'creation_form': creation_form,
        'join_form': join_form,
        'csrf_token': get_token(request)
    }
    
    response = render(request, 'expenses/group_setup.html', context)
    response.set_cookie('csrftoken', get_token(request), samesite='Lax')
    return response

@login_required
@csrf_protect
def create_group(request):
    # If user already has a group, redirect to dashboard
    if request.user.profile.group:
        return redirect('dashboard')
    
    if request.method == 'POST':
        creation_form = GroupCreationForm(request.POST)
        if creation_form.is_valid():
            group = creation_form.save()
            profile = request.user.profile
            profile.group = group
            profile.save()
            messages.success(request, f"Group '{group.name}' created successfully! Your group code is {group.code}")
            return redirect('dashboard')
    
    # If form is invalid or not a POST request, redirect back to setup
    return redirect('group_setup')

@login_required
@csrf_protect
def join_group(request):
    # If user already has a group, redirect to dashboard
    if request.user.profile.group:
        return redirect('dashboard')
    
    if request.method == 'POST':
        join_form = JoinGroupForm(request.POST)
        if join_form.is_valid():
            try:
                code = join_form.cleaned_data.get('code')
                group = Group.objects.get(code=code)
                profile = request.user.profile
                profile.group = group
                profile.save()
                messages.success(request, f"You have joined the group '{group.name}'!")
                return redirect('dashboard')
            except Group.DoesNotExist:
                messages.error(request, "Invalid group code. Please try again.")
        else:
            messages.error(request, "There was an error with your submission. Please try again.")
    
    # If form is invalid or not a POST request, redirect back to setup
    return redirect('group_setup')

@login_required
def dashboard(request):
    # If user doesn't have a group, redirect to group setup
    if not request.user.profile.group:
        messages.info(request, "You need to create or join a group first.")
        return redirect('group_setup')
    
    group = request.user.profile.group
    expenses = Expense.objects.filter(group=group).order_by('-date')[:10]
    members = User.objects.filter(profile__group=group)
    
    # Calculate balances
    balances = calculate_balances(group)
    
    # Format settlements for display
    settlements = calculate_settlements(balances)
    
    return render(request, 'expenses/dashboard.html', {
        'group': group,
        'expenses': expenses,
        'members': members,
        'balances': balances,
        'settlements': settlements
    })

@login_required
def expense_list(request):
    # If user doesn't have a group, redirect to group setup
    if not request.user.profile.group:
        messages.info(request, "You need to create or join a group first.")
        return redirect('group_setup')
    
    group = request.user.profile.group
    expenses = Expense.objects.filter(group=group).order_by('-date')
    
    return render(request, 'expenses/expense_list.html', {
        'expenses': expenses,
        'group': group
    })

@login_required
def add_expense(request):
    # If user doesn't have a group, redirect to group setup
    if not request.user.profile.group:
        messages.info(request, "You need to create or join a group first.")
        return redirect('group_setup')
    
    group = request.user.profile.group
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, group=group)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.group = group
            expense.save()
            form.save_m2m()  # Save the many-to-many data for the form
            messages.success(request, f"Expense '{expense.title}' added successfully!")
            return redirect('expense_list')
    else:
        form = ExpenseForm(group=group, initial={'paid_by': request.user})
    
    return render(request, 'expenses/add_expense.html', {'form': form})

@login_required
def edit_expense(request, expense_id):
    # If user doesn't have a group, redirect to group setup
    if not request.user.profile.group:
        messages.info(request, "You need to create or join a group first.")
        return redirect('group_setup')
    
    group = request.user.profile.group
    expense = get_object_or_404(Expense, id=expense_id, group=group)
    
    # Only the creator or payer can edit the expense
    if expense.paid_by != request.user:
        messages.error(request, "You don't have permission to edit this expense.")
        return redirect('expense_list')
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense, group=group)
        if form.is_valid():
            form.save()
            messages.success(request, f"Expense '{expense.title}' updated successfully!")
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense, group=group)
    
    return render(request, 'expenses/edit_expense.html', {'form': form, 'expense': expense})

@login_required
def delete_expense(request, expense_id):
    # If user doesn't have a group, redirect to group setup
    if not request.user.profile.group:
        messages.info(request, "You need to create or join a group first.")
        return redirect('group_setup')
    
    group = request.user.profile.group
    expense = get_object_or_404(Expense, id=expense_id, group=group)
    
    # Only the creator or payer can delete the expense
    if expense.paid_by != request.user:
        messages.error(request, "You don't have permission to delete this expense.")
        return redirect('expense_list')
    
    if request.method == 'POST':
        expense.delete()
        messages.success(request, f"Expense '{expense.title}' deleted successfully!")
        return redirect('expense_list')
    
    return render(request, 'expenses/delete_expense.html', {'expense': expense})

@login_required
def view_group(request):
    # If user doesn't have a group, redirect to group setup
    if not request.user.profile.group:
        messages.info(request, "You need to create or join a group first.")
        return redirect('group_setup')
    
    group = request.user.profile.group
    members = User.objects.filter(profile__group=group)
    
    return render(request, 'expenses/view_group.html', {
        'group': group,
        'members': members
    })

def calculate_balances(group):
    """Calculate the balance for each user in the group"""
    members = User.objects.filter(profile__group=group)
    balances = {member: Decimal('0.00') for member in members}
    
    expenses = Expense.objects.filter(group=group)
    
    for expense in expenses:
        # Amount paid by the user who created the expense
        balances[expense.paid_by] += expense.amount
        
        # Split amount among shared users
        shared_users = expense.shared_among.all()
        per_user = expense.amount / shared_users.count()
        
        for user in shared_users:
            balances[user] -= per_user
    
    return balances

def calculate_settlements(balances):
    """Calculate the optimal way to settle debts"""
    # Sort users by balance (descending)
    sorted_balances = sorted(balances.items(), key=lambda x: x[1], reverse=True)
    settlements = []
    
    # If all balances are close to zero, no settlements needed
    if all(abs(balance) < 0.01 for _, balance in sorted_balances):
        return settlements
    
    # Create a copy of sorted_balances that we can modify
    balances_copy = sorted_balances.copy()
    
    while len(balances_copy) > 1:
        # Get users with highest positive and lowest negative balances
        creditor, credit = balances_copy[0]
        debtor, debt = balances_copy[-1]
        
        if abs(credit) < 0.01 and abs(debt) < 0.01:
            # All balances are settled
            break
        
        # Calculate transfer amount
        amount = min(credit, abs(debt))
        
        if amount > 0.01:  # Only add settlements for significant amounts
            settlements.append({
                'from': debtor,
                'to': creditor,
                'amount': round(amount, 2)
            })
        
        # Update balances
        new_credit = credit - amount
        new_debt = debt + amount
        
        # Update the list and resort
        balances_copy[0] = (creditor, new_credit)
        balances_copy[-1] = (debtor, new_debt)
        balances_copy.sort(key=lambda x: x[1], reverse=True)
    
    return settlements
