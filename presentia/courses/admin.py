from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Curso, Nucleo, Aula
from presentia.attendance.models import Frequencia
from presentia.attendance.services import gerar_frequencia_em_lote

class FrequenciaInline(admin.TabularInline):
    model = Frequencia
    extra = 0
    fields = ('matricula', 'status')
    readonly_fields = ('matricula',)
    verbose_name = "Aluno Presente"
    verbose_name_plural = "Lista de Chamada (Marque os presentes)"

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('ordem', 'nome')
    ordering = ('ordem',)

@admin.register(Nucleo)
class NucleoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'igreja', 'curso')
    list_filter = ('curso', 'igreja')
    search_fields = ('nome', 'igreja__nome')

@admin.register(Aula)
class AulaAdmin(admin.ModelAdmin):
    list_display = ('data', 'nucleo', 'topico')
    list_filter = ('nucleo', 'data')
    inlines = [FrequenciaInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not change:
            gerar_frequencia_em_lote(form.instance)
            
    # Adiciona o seletor no topo da lista de aulas tambem
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['nucleos'] = Nucleo.objects.all()
        extra_context['nucleo_ativo'] = request.GET.get('nucleo_ativo', '')
        return super().changelist_view(request, extra_context=extra_context)


