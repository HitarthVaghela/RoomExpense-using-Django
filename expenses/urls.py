from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView

class LogoutViewAllowGet(LogoutView):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

urlpatterns = [
    # Authentication routes
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', LogoutViewAllowGet.as_view(next_page='login'), name='logout'),
    
    # Group management
    path('group/setup/', views.group_setup, name='group_setup'),
    path('group/create/', views.create_group, name='create_group'),
    path('group/join/', views.join_group, name='join_group'),
    path('group/view/', views.view_group, name='view_group'),
    
    # Dashboard and expenses
    path('', views.dashboard, name='dashboard'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/edit/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('expenses/delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
] 