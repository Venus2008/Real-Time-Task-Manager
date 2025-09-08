from django.contrib import admin
from task.models import Task,TaskUpdate


class TaskAdmin(admin.ModelAdmin):
    # Fields visible in the list page
    list_display = (
        "id","title","status","priority","created_by","assigned_to","created_at","updated_at",)

    # Add filters on the right sidebar
    list_filter = ("status","priority","created_at","updated_at","created_by","assigned_to",)

    #  Add search bar (searchable fields)
    search_fields = ("title", "description", "created_by__username", "assigned_to__username")

    # Organize fields in edit page
    fieldsets = (
        ("Task Info", {
            "fields": ("title", "description", "status", "priority", "file")
        }),
        ("Relations", {
            "fields": ("created_by", "assigned_to")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),  # hide by default
        }),
    )

    # Read-only fields
    readonly_fields = ("created_at", "updated_at")

    # Default ordering
    ordering = ("-created_at",)

    # Optional: show nice dropdowns for relations
    autocomplete_fields = ("created_by", "assigned_to")

class TaskUpdateAdmin(admin.ModelAdmin):
    list_display = ("task", "updated_by", "status", "short_comment", "created_at")

    list_filter = ("status", "created_at", "updated_by")
    
    search_fields = ("task__title", "updated_by__email", "comment")
    
    ordering = ("-created_at",)
    
    autocomplete_fields = ("task", "updated_by")
    
    date_hierarchy = "created_at"

    def short_comment(self, obj):
        """Show only first 40 chars of the comment"""
        return (obj.comment[:20] + "...") if obj.comment and len(obj.comment) > 40 else obj.comment
    short_comment.short_description = "Comment"


admin.site.register(Task,TaskAdmin)
admin.site.register(TaskUpdate,TaskUpdateAdmin)
