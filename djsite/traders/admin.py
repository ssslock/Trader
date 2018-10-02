from django.contrib import admin

from .models import Exchange, Trader, Balance

admin.site.register(Exchange)


class BalanceInline(admin.StackedInline):
    model = Balance
    extra = 3


class TraderAdmin(admin.ModelAdmin):
    # fieldsets = [
    #     (None,               {'fields': ['question_text']}),
    #     ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
    # ]
    inlines = [BalanceInline]

admin.site.register(Trader, TraderAdmin)