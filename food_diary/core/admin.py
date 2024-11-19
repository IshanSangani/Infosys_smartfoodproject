from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'date_of_birth', 'height', 'weight', 'gender', 'daily_calorie_goal')
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Info', {
            'fields': ('date_of_birth', 'height', 'weight', 'gender', 'daily_calorie_goal')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile Info', {
            'fields': ('date_of_birth', 'height', 'weight', 'gender', 'daily_calorie_goal')
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
