from django.contrib import admin
from task.models import Task


class TaskAdmin(admin.ModelAdmin):
    # Fields visible in the list page
    list_display = (
        "id","title","status","priority","created_by","assigned_to","created_at","updated_at","due_date")

    # Add filters on the right sidebar
    list_filter = ("status","priority","created_at","updated_at","created_by","assigned_to","due_date")

    #  Add search bar (searchable fields)
    search_fields = ("title", "description", "created_by__username", "assigned_to__username","due_date")

    # Organize fields in edit page
    fieldsets = (
        ("Task Info", {
            "fields": ("title", "description", "status", "priority", "file","is_archived","due_date")
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



admin.site.register(Task,TaskAdmin)

