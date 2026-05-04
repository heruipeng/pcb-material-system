from django.contrib import admin
from .models import Report, ReportCategory, ReportInstance, Dashboard, ScheduledReport


@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sort_order', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'report_type', 'is_active', 'created_by', 'created_at']
    list_filter = ['report_type', 'is_active']
    search_fields = ['name', 'code']


@admin.register(ReportInstance)
class ReportInstanceAdmin(admin.ModelAdmin):
    list_display = ['report', 'name', 'status', 'row_count', 'generated_by', 'generated_at']
    list_filter = ['status']
    date_hierarchy = 'generated_at'


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_public', 'created_by', 'created_at']
    list_filter = ['is_public']


@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    list_display = ['report', 'name', 'frequency', 'is_active', 'last_executed']
    list_filter = ['frequency', 'is_active']
