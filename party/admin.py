from django.contrib import admin
from .models import Party

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'representative', 'phone', 'email', 'business_number', 'is_active')
    search_fields = ('name', 'representative', 'business_number')
    list_filter = ('is_active',)
    ordering = ('name',)