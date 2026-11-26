from django.contrib import admin
from .models import Curso, Nucleo, Turma, Aula

# O admin nativo do Django nao e usado para estes models (usamos views customizadas)
# @admin.register(Nucleo)
# class NucleoAdmin(admin.ModelAdmin):
#     pass