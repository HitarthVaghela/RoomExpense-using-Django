from django.contrib import admin
from .models import Group, UserProfile, Expense

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'group')
    list_filter = ('group',)
    search_fields = ('user__username', 'group__name')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'paid_by', 'date', 'group')
    list_filter = ('date', 'group')
    search_fields = ('title', 'paid_by__username', 'group__name')
    filter_horizontal = ('shared_among',)
