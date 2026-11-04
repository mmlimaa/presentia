from django.contrib import admin
from .models import Matricula, Frequencia

@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'nucleo')
    list_filter = ('nucleo',)
    search_fields = ('aluno__nome',)

@admin.register(Frequencia)
class FrequenciaAdmin(admin.ModelAdmin):
    list_display = ('aula', 'matricula', 'status')
    list_filter = ('aula__nucleo', 'status')
    search_fields = ('matricula__aluno__nome',)
    ordering = ('aula', 'matricula__aluno__nome')


