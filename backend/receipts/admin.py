from django.contrib import admin

from .models import ReceiptText


@admin.register(ReceiptText)
class ReceiptTextAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_filename', 'created_at')
    search_fields = ('original_filename', 'text')
    readonly_fields = ('created_at',)
