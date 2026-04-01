from django.contrib import admin
from .models import Account, JournalEntry, JournalLine

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "type")
    search_fields = ("code", "name")
    list_filter = ("type",)

class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 1

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "description")
    inlines = [JournalLineInline]
    search_fields = ("description",)
    ordering = ("-date",)

@admin.register(JournalLine)
class JournalLineAdmin(admin.ModelAdmin):
    list_display = ("entry", "account", "party", "debit", "credit")
    search_fields = ("account__name", "party__name")
    list_filter = ("account",)