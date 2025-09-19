from django.contrib import admin
from .models import Receipt


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    """Admin configuration for Receipt model."""
    
    list_display = [
        'id', 
        'user', 
        'restaurant_name', 
        'date', 
        'price',
        'created_at'
    ]
    list_filter = ['date', 'created_at', 'user']
    search_fields = ['restaurant_name', 'address', 'user__email']
    ordering = ['-date', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'date', 'price')
        }),
        ('Restaurant Details', {
            'fields': ('restaurant_name', 'address')
        }),
        ('Image', {
            'fields': ('image',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
