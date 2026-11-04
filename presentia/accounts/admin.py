from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Usuario, Aluno
from presentia.courses.models import Nucleo

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'perfil', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (('Perfil FVC', {'fields': ('perfil', 'telefone', 'nucleo_padrao')}),)

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'data_inicio')
    search_fields = ('nome', 'email')
    ordering = ('nome',)
    
    # Adiciona o seletor de nucleo no topo da lista de alunos
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['nucleos'] = Nucleo.objects.all()
        extra_context['nucleo_ativo'] = request.GET.get('nucleo_ativo', '')
        return super().changelist_view(request, extra_context=extra_context)


