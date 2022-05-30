from django.contrib import admin
import datetime
from .models import SubRubric, SuperRubric, Comment
from .form import SubRubricForm
from .models import AdvUser, Bb, AdditionalImage
from .utilities import send_activation_notification


def send_activation_notifications(modeladmin, request, queryset):
    for rec in queryset:
        if not rec.is_activatadet:
            send_activation_notification(rec)
    modeladmin.message_user(request, 'Письмо с требованиями отправлены')


send_activation_notification.short_description = 'Отправка писем с требованиями активации'


class NonactivatedFilter(admin.SimpleListFilter):
    title = 'прошли активацию?'
    parameter_name = 'actstate'

    def lookups(self, request, model_admin):
        return (('activated', 'прошли', 'threedays', 'не прошли более 3 дней'), ('week', 'не прошли более недели'),)

    def queryset(self, request, queryset):
        val = self.value()
        if val == 'activated':
            return queryset.filter(is_active=True, is_activated=True)
        elif val == 'threedays':
            d = datetime.date.today() - datetime.timedelta(days=3)
            return queryset.filter(is_active=False, is_activated=False,
                                   date_joined_date_it=d)
        elif val == 'week':
            d = datetime.date.today() - datetime.timedelta(weeks=3)
            return queryset.filter(is_active=False, is_activated=False,
                                   date_joined_date_it=d)


class AdvUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_activated', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = (NonactivatedFilter,)
    fields = (('username', 'email'), ('first_name', 'last_name'),
              ('send_messages', 'is_active', 'is_activated'), ('is_staff', 'is_superuser'),
              'groups', 'user_permissions', ('last_login', 'date_joined'))
    readonly_fields = ('last_login', 'date_joined')
    actions = (send_activation_notifications,)


admin.site.register(AdvUser, AdvUserAdmin)


class SubRubricInline(admin.TabularInline):
    model = SubRubric


class SuperRubricAdmin(admin.ModelAdmin):
    exclude = ('super_rubric',)
    inlines = (SubRubricInline,)


admin.site.register(SuperRubric, SuperRubricAdmin)


class SubRubricAdmin(admin.ModelAdmin):
    form = SubRubricForm


admin.site.register(SubRubric, SubRubricAdmin)


class AdditionalImageInline(admin.TabularInline):
    model = AdditionalImage


class BbAdmin(admin.ModelAdmin):
    list_display = ('rubric', 'title', 'content', 'author', 'created_at')
    fields = (('rubric', 'author'), 'title', 'content', 'price', 'contacts', 'image', 'is_active')
    inlines = (AdditionalImageInline,)


admin.site.register(Bb, BbAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'content', 'created_at', 'is_active')
    list_display_links = ('author', 'content')
    list_filter = ('is_active',)
    search_fields = ('author', 'content',)
    date_hierarchy = 'created_at'
    fields = ('author', 'content', 'is_active', 'created_at')
    readonly_fields = ('created_at',)


admin.site.register(Comment, CommentAdmin)
