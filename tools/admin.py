from django.contrib import admin
from .models import Tool, ToolCategory, ToolExecution, ToolTemplate, ToolOutput


@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sort_order', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'tool_type', 'version', 'is_active']
    list_filter = ['tool_type', 'is_active']
    search_fields = ['name', 'code']


@admin.register(ToolExecution)
class ToolExecutionAdmin(admin.ModelAdmin):
    list_display = ['tool', 'material', 'status', 'executor', 'created_at']
    list_filter = ['status', 'tool']
    date_hierarchy = 'created_at'


@admin.register(ToolTemplate)
class ToolTemplateAdmin(admin.ModelAdmin):
    list_display = ['tool', 'name', 'is_default', 'created_by', 'created_at']
    list_filter = ['is_default']


@admin.register(ToolOutput)
class ToolOutputAdmin(admin.ModelAdmin):
    list_display = ['execution', 'output_type', 'name', 'created_at']
    list_filter = ['output_type']
