from django.contrib import admin
from .models import Usuario, SolicitacaoAcesso, Aluno

# O admin nativo do Django nao e usado para estes models (usamos views customizadas)
# @admin.register(Usuario)
# class CustomUserAdmin(admin.ModelAdmin):
#     pass