from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from .models import Igreja

class IgrejaForm(forms.ModelForm):
    nome = forms.CharField(widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}))
    cidade = forms.CharField(widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}))
    endereco = forms.CharField(widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}))

    class Meta:
        model = Igreja
        fields = ['nome', 'cidade', 'endereco']

def lista_igrejas(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    igrejas = Igreja.objects.all().order_by('nome')
    return render(request, 'igrejas_lista.html', {'igrejas': igrejas})

def nova_igreja(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    if request.method == 'POST':
        form = IgrejaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Igreja cadastrada com sucesso!")
            return redirect('igrejas_lista')
    else:
        form = IgrejaForm()
    return render(request, 'igreja_form.html', {'form': form})




from django.shortcuts import get_object_or_404
from presentia.courses.models import Nucleo

def editar_igreja(request, igreja_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    igreja = get_object_or_404(Igreja, id=igreja_id)
    
    if request.method == 'POST':
        form = IgrejaForm(request.POST, instance=igreja)
        if form.is_valid():
            form.save()
            messages.success(request, "Igreja atualizada com sucesso!")
            return redirect('igrejas_lista')
    else:
        form = IgrejaForm(instance=igreja)
        
    return render(request, 'igreja_form.html', {'form': form, 'igreja': igreja})

def excluir_igreja(request, igreja_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    igreja = get_object_or_404(Igreja, id=igreja_id)
    
    # Regra de Negocio: Nao permitir excluir se tiver nucleos vinculados
    if Nucleo.objects.filter(igreja=igreja).exists():
        messages.error(request, "Não é possível excluir esta igreja, pois ela possui núcleos vinculados.")
        return redirect('igrejas_lista')
        
    if request.method == 'POST':
        nome = igreja.nome
        igreja.delete()
        messages.success(request, f"Igreja {nome} excluída com sucesso!")
        return redirect('igrejas_lista')
        
    return render(request, 'confirmar_exclusao_igreja.html', {'igreja': igreja})
