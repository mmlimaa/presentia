from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django import forms
from django.db.models import Count
from .models import Curso, Nucleo
from presentia.churches.models import Igreja
from presentia.attendance.models import Matricula

class NucleoForm(forms.ModelForm):
    nome = forms.CharField(widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}))
    igreja = forms.ModelChoiceField(queryset=Igreja.objects.all(), widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}))

    class Meta:
        model = Nucleo
        fields = ['nome', 'igreja']

def lista_nucleos(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
        
    from django.db import connection
    from presentia.churches.models import Igreja
    
    # Pega todas as igrejas para o filtro
    igrejas = Igreja.objects.all().order_by('nome')
    
    # Pega o filtro da URL
    igreja_filtro = request.GET.get('igreja')
    
    query = '''
        SELECT n.id, n.nome, i.id as igreja_id, i.nome AS igreja_nome, i.cidade,
               (SELECT COUNT(*) FROM tb_matriculas m WHERE m.nucleo_id = n.id) AS total_alunos,
               (SELECT COUNT(*) FROM tb_turmas t WHERE t.nucleo_id = n.id) AS total_turmas
        FROM tb_nucleos n
        JOIN tb_igrejas i ON i.id = n.igreja_id
    '''
    params = []
    
    if igreja_filtro:
        query += " WHERE i.id = %s::uuid"
        params.append(igreja_filtro)
        
    query += " ORDER BY n.nome"
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()

    nucleos = []
    for row in rows:
        nucleos.append({
            'id': row[0],
            'nome': row[1],
            'igreja_nome': row[3],
            'cidade': row[4],
            'total_alunos': row[5],
            'total_turmas': row[6],
        })

    return render(request, 'nucleos_lista.html', {
        'nucleos': nucleos, 
        'igrejas': igrejas,
        'igreja_filtro': igreja_filtro
    })


def novo_nucleo(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    if request.method == 'POST':
        form = NucleoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Núcleo cadastrado com sucesso!")
            return redirect('nucleos_lista')
    else:
        form = NucleoForm()
    return render(request, 'nucleo_form.html', {'form': form})




from django import forms
from presentia.courses.models import Turma

class TurmaForm(forms.ModelForm):
    nome = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}))
    nucleo = forms.ModelChoiceField(queryset=Nucleo.objects.all(), widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}))
    curso = forms.ModelChoiceField(queryset=Curso.objects.all().order_by('ordem'), widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}))
    
    # Adiciona o formato '%Y-%m-%d' para o Django entender a data no HTML
    data_inicio = forms.DateField(
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'type': 'date'}
        ), 
        input_formats=['%Y-%m-%d']
    )
    data_fim = forms.DateField(
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'type': 'date'}
        ),
        input_formats=['%Y-%m-%d']
    )

    class Meta:
        model = Turma
        fields = ['nome', 'nucleo', 'curso', 'data_inicio', 'data_fim']

class Meta:
        model = Turma
        fields = ['nome', 'nucleo', 'curso', 'data_inicio', 'data_fim']

def lista_turmas(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    turmas = Turma.objects.all().select_related('nucleo', 'curso').order_by('-data_inicio')
    return render(request, 'turmas_lista.html', {'turmas': turmas})

def nova_turma(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    if request.method == 'POST':
        form = TurmaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Turma cadastrada com sucesso!")
            return redirect('turmas_lista')
    else:
        form = TurmaForm()
    return render(request, 'turma_form.html', {'form': form})


# --- EDICAO E EXCLUSAO DE TURMA ---
def editar_turma(request, turma_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    turma = get_object_or_404(Turma, id=turma_id)
    
    if request.method == 'POST':
        form = TurmaForm(request.POST, instance=turma)
        if form.is_valid():
            form.save()
            messages.success(request, "Turma atualizada com sucesso!")
            return redirect('turmas_lista')
    else:
        form = TurmaForm(instance=turma)
        
    return render(request, 'turma_form.html', {'form': form, 'turma': turma})

def excluir_turma(request, turma_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    turma = get_object_or_404(Turma, id=turma_id)
    
    # Regra de Negocio: Nao permitir excluir se tiver alunos
    from presentia.attendance.models import Matricula
    if Matricula.objects.filter(turma=turma).exists():
        messages.error(request, "Não é possível excluir esta turma, pois ela possui alunos matriculados.")
        return redirect('turmas_lista')
    
    if request.method == 'POST':
        nome = turma.nome
        turma.delete()
        messages.success(request, f"Turma {nome} excluída com sucesso!")
        return redirect('turmas_lista')
        
    return render(request, 'confirmar_exclusao_turma.html', {'turma': turma})


from django.http import JsonResponse

def api_contar_turmas(request, nucleo_id):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM tb_turmas WHERE nucleo_id = %s::uuid", [str(nucleo_id)])
        total = cursor.fetchone()[0]
    return JsonResponse({'total': total})
