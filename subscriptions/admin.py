from django.contrib import admin
from .models import (
    PlanDuration,
    FreeBorrowingPlan,
    BundleBorrowingPlan,
    Subscription
)

@admin.register(PlanDuration)
class PlanDurationAdmin(admin.ModelAdmin):
    list_display = ('months', 'description')
    search_fields = ('description',)

class BasePlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'price', 'is_active')
    list_filter = ('duration', 'is_active')
    search_fields = ('name', 'description')

@admin.register(FreeBorrowingPlan)
class FreeBorrowingPlanAdmin(BasePlanAdmin):
    list_display = BasePlanAdmin.list_display + ('max_books',)

@admin.register(BundleBorrowingPlan)
class BundleBorrowingPlanAdmin(BasePlanAdmin):
    list_display = BasePlanAdmin.list_display + ('max_bundles',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'get_plans_display',
        'start_date',
        'end_date',
        'status',
        'is_active'
    )
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('user__username', 'user__email')
    raw_id_fields = ('user',)
    
    def get_plans_display(self, obj):
        plans = []
        if obj.free_borrowing_plan:
            plans.append(f"Free: {obj.free_borrowing_plan.name}")
        if obj.bundle_borrowing_plan:
            plans.append(f"Bundle: {obj.bundle_borrowing_plan.name}")
        return " + ".join(plans)
    get_plans_display.short_description = "Plans"
