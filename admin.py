from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.http import JsonResponse
from django.utils.html import format_html

from .models import Analysis, Result

# Register your models here.


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    def run_analyse(self, obj):
        return format_html(
            """
                <a class="button daddy-green" onclick="analyse('{pk}')">
                    Analyse
                </a>
            """,
            pk=str(obj.pk),
        )

    list_display = (
        "__str__",
        "user",
        "register_date",
        "ip",
        "is_completed",
        # "result",
        "run_analyse",
    )
    ordering = ("-register_date",)
    search_fields = ("user__email",)

    change_list_template = (
        settings.PROJECT_ROOT + "/analysis/templates/analysis_list.html"
    )

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("analyse/<str:analysis_id>/", self.analyse),
        ]
        return my_urls + urls

    def analyse(self, request, analysis_id):
        analysis = Analysis.objects.get(id=analysis_id)
        data = analysis.re_analyse()
        return JsonResponse(data)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_select_related = True
    list_display = (
        "__str__",
        "_get_user",
        "register_date",
        "sp",
        "dp",
        "spo2",
        "hr",
        "detail",
        "_status",
    )
    # list_filter = ("level__title",)
    list_per_page = 30
    ordering = ("-register_date",)
    search_fields = ("analysis__id",)

    def _status(self, obj):  # TODO This method should be developed further
        return format_html(
            '<div style="width:100%%; height:100%%; background-color:orange;">{}</div>',
            obj.__str__(),
        )

    _status.short_description = "Status"

    def _get_user(self, obj):
        return obj.analysis.user

    _get_user.short_description = "User"