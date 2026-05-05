from django.contrib import admin
from .models import ProductionJob


@admin.register(ProductionJob)
class ProductionJobAdmin(admin.ModelAdmin):
    list_display = ['job_no', 'serial_no', 'material_no', 'tool_type', 'status', 'posted_at', 'completed_at']
    list_filter = ['status', 'tool_type', 'factory']
    search_fields = ['job_no', 'serial_no', 'material_no']
    readonly_fields = ['created_at', 'updated_at']
