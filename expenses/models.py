from django.db import models
from django.contrib.auth.models import User
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Group(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=12, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(uuid.uuid4()).replace('-', '')[:12].upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class Expense(models.Model):
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paid_expenses')
    date = models.DateField(auto_now_add=True)
    shared_among = models.ManyToManyField(User, related_name='shared_expenses')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.amount}"
    
    class Meta:
        ordering = ['-date']

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
