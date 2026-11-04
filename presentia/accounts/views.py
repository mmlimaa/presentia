from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django import forms
from .models import Usuario, SolicitacaoAcesso, Aluno
from presentia.courses.models import Nucleo, Curso
from presentia.attendance.models import Matricula, AlunoExperimental
from django.contrib.auth.hashers import make_password

# --- FORMULÁRIO DE SOLICITAÇÃO DE ACESSO ---
class SolicitacaoAcessoForm(forms.ModelForm):
    nome_completo = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': 'NOME COMPLETO'}))
    login = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': 'login'}))
    senha = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': 'Senha (6 a 16 caracteres)'}), min_length=6, max_length=16, required=True)
    email = forms.EmailField(max_length=100, required=True, widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': 'email@exemplo.com'}))
    telefone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': '(11) 99999-9999'}))

    class Meta:
        model = SolicitacaoAcesso
        fields = ['nome_completo', 'login', 'email', 'telefone']

    def clean_nome_completo(self):
        nome = self.cleaned_data.get('nome_completo')
        return nome.upper() if nome else nome

    def clean_login(self):
        login = self.cleaned_data.get('login')
        if login:
            login = login.lower()
            if Usuario.objects.filter(login=login).exists() or SolicitacaoAcesso.objects.filter(login=login).exists():
                raise forms.ValidationError("Este login já está em uso ou em análise.")
        return login

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            if Usuario.objects.filter(email=email).exists() or SolicitacaoAcesso.objects.filter(email=email).exists():
                raise forms.ValidationError("Este e-mail já está cadastrado ou em análise.")
        return email

    def save(self, commit=True):
        solicitacao = super().save(commit=False)
        solicitacao.senha_hash = make_password(self.cleaned_data['senha'])
        if commit:
            solicitacao.save()
        return solicitacao

# --- VIEWS DE AUTENTICAÇÃO ---
def login_view(request):
    if request.session.get('usuario_id'):
        return redirect('dashboard')

    if request.method == 'POST':
        login_digitado = request.POST.get('username', '').strip().lower()
        senha_digitada = request.POST.get('password', '').strip()

        if not login_digitado or not senha_digitada:
            messages.error(request, "Por favor, preencha todos os campos.")
            return render(request, 'login.html')

        try:
            user = Usuario.objects.get(login=login_digitado)
            if user.check_senha(senha_digitada):
                request.session['usuario_id'] = user.id
                request.session['usuario_nome'] = user.nome_completo
                request.session['usuario_is_admin'] = user.is_admin
                return redirect('dashboard')
            else:
                messages.error(request, "Senha incorreta.")
        except Usuario.DoesNotExist:
            messages.error(request, "Usuário não encontrado.")
            
    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

class SolicitacaoAcessoView(CreateView):
    form_class = SolicitacaoAcessoForm
    template_name = 'solicitar_acesso.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.success(self.request, "Solicitação enviada com sucesso! Aguarde a aprovação.")
        return super().form_valid(form)

# --- FORMULÁRIO E VIEWS DE ALUNO ---
class AlunoForm(forms.ModelForm):
    nome = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-blue-500', 'placeholder': 'Nome completo'}))
    telefone = forms.CharField(max_length=11, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-blue-500', 'placeholder': '11999999999'}))
    email = forms.EmailField(max_length=100, required=True, widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-blue-500', 'placeholder': 'email@exemplo.com'}))
    data_inicio = forms.DateField(
        widget=forms.DateInput(
            format='%Y-%m-%d', 
            attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-blue-500', 'type': 'date'}
        ), 
        label="Data de Matrícula"
    )

    class Meta:
        model = Aluno
        fields = ['nome', 'telefone', 'email', 'data_inicio']

    def clean_telefone(self):
        tel = self.cleaned_data.get('telefone')
        if tel:
            tel = ''.join(filter(str.isdigit, tel))
            if len(tel) != 11:
                raise forms.ValidationError("O telefone deve ter 11 dígitos (DDD + número).")
        return tel

def alunos_nucleo(request, nucleo_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    nucleo = get_object_or_404(Nucleo, id=nucleo_id)
    cursos = Curso.objects.all().order_by('ordem')
    
    # Se nenhum curso foi selecionado, pega o primeiro por padrao
    curso_id = request.GET.get('curso')
    if curso_id:
        curso_selecionado = get_object_or_404(Curso, id=curso_id)
    else:
        curso_selecionado = cursos.first()
        
    if curso_selecionado:
        matriculas = Matricula.objects.filter(nucleo=nucleo, curso=curso_selecionado).select_related('aluno').order_by('aluno__nome')
        experimentais = AlunoExperimental.objects.filter(nucleo=nucleo, curso=curso_selecionado).order_by('-data_visita')
    else:
        matriculas = Matricula.objects.none()
        experimentais = AlunoExperimental.objects.none()
    
    return render(request, 'alunos_nucleo.html', {
        'nucleo': nucleo, 
        'matriculas': matriculas, 
        'experimentais': experimentais,
        'cursos': cursos,
        'curso_selecionado': curso_selecionado
    })


def novo_aluno_nucleo(request, nucleo_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    nucleo = get_object_or_404(Nucleo, id=nucleo_id)
    curso_id = request.GET.get('curso')
    curso = get_object_or_404(Curso, id=curso_id) if curso_id else None
    
    if not curso:
        messages.error(request, "Por favor, selecione um período antes de matricular.")
        return redirect('alunos_nucleo', nucleo_id=nucleo.id)
    
    if request.method == 'POST':
        form = AlunoForm(request.POST)
        if form.is_valid():
            aluno = form.save()
            Matricula.objects.create(aluno=aluno, nucleo=nucleo, curso=curso)
            messages.success(request, f"Aluno matriculado com sucesso no período {curso.nome}!")
            return redirect(f"/nucleos/{nucleo.id}/alunos/?curso={curso.id}")
    else:
        form = AlunoForm()
        
    return render(request, 'aluno_form.html', {'form': form, 'nucleo': nucleo, 'curso': curso})

def editar_aluno(request, aluno_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    aluno = get_object_or_404(Aluno, id=aluno_id)
    nucleo_id = request.GET.get('nucleo_id') or request.POST.get('nucleo_id')
    nucleo = get_object_or_404(Nucleo, id=nucleo_id) if nucleo_id else None
    
    if request.method == 'POST':
        form = AlunoForm(request.POST, instance=aluno)
        if form.is_valid():
            form.save()
            messages.success(request, "Dados do aluno atualizados com sucesso!")
            curso_id = request.GET.get('curso_id') or request.POST.get('curso_id')
            if nucleo_id and curso_id:
                return redirect(f"/nucleos/{nucleo_id}/alunos/?curso={curso_id}")
            elif nucleo_id:
                return redirect('alunos_nucleo', nucleo_id=nucleo_id)
            return redirect('dashboard')
    else:
        form = AlunoForm(instance=aluno)
        
    return render(request, 'aluno_editar.html', {'form': form, 'aluno': aluno, 'nucleo': nucleo})

# --- ALUNOS EXPERIMENTAIS ---
class AlunoExperimentalForm(forms.ModelForm):
    nome_completo = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-blue-500', 'placeholder': 'Nome completo'}))
    celular = forms.CharField(max_length=11, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-blue-500', 'placeholder': '11999999999'}))

    class Meta:
        model = AlunoExperimental
        fields = ['nome_completo', 'celular']

    def clean_celular(self):
        celular = self.cleaned_data.get('celular')
        if celular:
            celular = ''.join(filter(str.isdigit, celular))
            if len(celular) != 11:
                raise forms.ValidationError("O celular deve ter 11 dígitos (DDD + número).")
            if AlunoExperimental.objects.filter(celular=celular).exists():
                raise forms.ValidationError("Este celular já foi utilizado em uma aula experimental anteriormente. O aluno deve ser matriculado como regular.")
        return celular

def novo_aluno_experimental(request, nucleo_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    nucleo = get_object_or_404(Nucleo, id=nucleo_id)
    curso_id = request.GET.get('curso')
    curso = get_object_or_404(Curso, id=curso_id) if curso_id else None
    
    if not curso:
        messages.error(request, "Por favor, selecione um período antes de cadastrar um aluno experimental.")
        return redirect('alunos_nucleo', nucleo_id=nucleo.id)

    if request.method == 'POST':
        form = AlunoExperimentalForm(request.POST)
        if form.is_valid():
            aluno = form.save(commit=False)
            aluno.nucleo = nucleo
            aluno.curso = curso
            aluno.save()
            messages.success(request, f"Aula experimental registrada com sucesso no período {curso.nome}!")
            return redirect(f"/nucleos/{nucleo.id}/alunos/?curso={curso.id}")
    else:
        form = AlunoExperimentalForm()
        
    return render(request, 'experimental_form.html', {'form': form, 'nucleo': nucleo, 'curso': curso})


# --- GESTAO DE SOLICITACOES DE ACESSO ---
def gerenciar_solicitacoes(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    # Apenas admin pode acessar
    if not request.session.get('usuario_is_admin'):
        messages.error(request, "Acesso negado. Apenas administradores podem gerenciar solicitações.")
        return redirect('dashboard')
        
    solicitacoes = SolicitacaoAcesso.objects.all().order_by('-data_solicitacao')
    return render(request, 'gerenciar_solicitacoes.html', {'solicitacoes': solicitacoes})

def aprovar_solicitacao(request, solicitacao_id):
    if not request.session.get('usuario_id') or not request.session.get('usuario_is_admin'):
        return redirect('login')
        
    solicitacao = get_object_or_404(SolicitacaoAcesso, id=solicitacao_id)
    
    if request.method == 'POST':
        # Cria o usuario na tabela oficial
        novo_usuario = Usuario(
            nome_completo=solicitacao.nome_completo,
            login=solicitacao.login,
            senha_hash=solicitacao.senha_hash, # Ja esta criptografada
            email=solicitacao.email,
            telefone=solicitacao.telefone,
            is_admin=False # Por padrao nao e admin
        )
        novo_usuario.save()
        
        # Apaga a solicitacao para nao acumular lixo
        solicitacao.delete()
        
        messages.success(request, f"Usuário {novo_usuario.nome_completo} aprovado com sucesso!")
        return redirect('gerenciar_solicitacoes')
        
    return render(request, 'confirmar_aprovacao.html', {'solicitacao': solicitacao})

def recusar_solicitacao(request, solicitacao_id):
    if not request.session.get('usuario_id') or not request.session.get('usuario_is_admin'):
        return redirect('login')
        
    solicitacao = get_object_or_404(SolicitacaoAcesso, id=solicitacao_id)
    
    if request.method == 'POST':
        nome = solicitacao.nome_completo
        solicitacao.delete()
        messages.warning(request, f"Solicitação de {nome} recusada e removida.")
        return redirect('gerenciar_solicitacoes')
        
    return render(request, 'confirmar_recusa.html', {'solicitacao': solicitacao})


# --- ADMINISTRACAO DE USUARIOS ---
def gerenciar_usuarios(request):
    if not request.session.get('usuario_id') or not request.session.get('usuario_is_admin'):
        return redirect('login')
        
    usuarios = Usuario.objects.all().order_by('nome_completo')
    return render(request, 'gerenciar_usuarios.html', {'usuarios': usuarios})

def resetar_senha(request, usuario_id):
    if not request.session.get('usuario_id') or not request.session.get('usuario_is_admin'):
        return redirect('login')
        
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha')
        if len(nova_senha) < 6 or len(nova_senha) > 16:
            messages.error(request, "A senha deve ter entre 6 e 16 caracteres.")
        else:
            usuario.set_senha(nova_senha)
            usuario.save()
            messages.success(request, f"Senha do usuário {usuario.nome_completo} redefinida com sucesso!")
            return redirect('gerenciar_usuarios')
            
    return render(request, 'resetar_senha.html', {'usuario': usuario})

def alternar_admin(request, usuario_id):
    if not request.session.get('usuario_id') or not request.session.get('usuario_is_admin'):
        return redirect('login')
        
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # Nao permite que o admin logado remova seu proprio privilegio
    if usuario.id == request.session.get('usuario_id'):
        messages.error(request, "Você não pode remover seu próprio status de administrador.")
        return redirect('gerenciar_usuarios')
        
    usuario.is_admin = not usuario.is_admin
    usuario.save()
    
    status = "promovido a" if usuario.is_admin else "rebaixado de"
    messages.success(request, f"Usuário {usuario.nome_completo} {status} Administrador.")
    return redirect('gerenciar_usuarios')

def excluir_usuario(request, usuario_id):
    if not request.session.get('usuario_id') or not request.session.get('usuario_is_admin'):
        return redirect('login')
        
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if usuario.id == request.session.get('usuario_id'):
        messages.error(request, "Você não pode excluir sua própria conta.")
        return redirect('gerenciar_usuarios')
        
    if request.method == 'POST':
        nome = usuario.nome_completo
        usuario.delete()
        messages.warning(request, f"Usuário {nome} excluído do sistema.")
        return redirect('gerenciar_usuarios')
        
    return render(request, 'confirmar_exclusao_usuario.html', {'usuario': usuario})


# --- EDICAO DE USUARIO ---
class EditarUsuarioForm(forms.ModelForm):
    nome_completo = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-blue-500'}))
    login = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-blue-500'}))
    email = forms.EmailField(max_length=100, required=True, widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-blue-500'}))
    telefone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-blue-500'}))

    class Meta:
        model = Usuario
        fields = ['nome_completo', 'login', 'email', 'telefone']

    def clean_login(self):
        login = self.cleaned_data.get('login', '').lower()
        # Verifica se o login ja existe em outro usuario
        if Usuario.objects.filter(login=login).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Este login ja esta em uso por outro usuario.")
        return login

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if Usuario.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Este e-mail ja esta cadastrado para outro usuario.")
        return email

def editar_usuario(request, usuario_id):
    if not request.session.get('usuario_id') or not request.session.get('usuario_is_admin'):
        return redirect('login')
        
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f"Dados do usuario {usuario.nome_completo} atualizados com sucesso!")
            return redirect('gerenciar_usuarios')
    else:
        form = EditarUsuarioForm(instance=usuario)
        
    return render(request, 'editar_usuario.html', {'form': form, 'usuario': usuario})




from presentia.courses.models import Turma

# --- ALUNOS DA TURMA ---
def alunos_turma(request, turma_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    turma = get_object_or_404(Turma, id=turma_id)
    
    # Pega o filtro da URL (padrao: todos)
    status_filtro = request.GET.get('status', 'todos')
    
    # Query base
    matriculas = Matricula.objects.filter(turma=turma).select_related('aluno').order_by('aluno__nome')
    
    # Aplica o filtro
    if status_filtro == 'ativos':
        matriculas = matriculas.filter(ativo=True)
    elif status_filtro == 'desligados':
        matriculas = matriculas.filter(ativo=False)
    
    experimentais = AlunoExperimental.objects.filter(nucleo=turma.nucleo, curso=turma.curso).order_by('-data_visita')
    
    return render(request, 'alunos_turma.html', {
        'turma': turma,
        'matriculas': matriculas,
        'experimentais': experimentais,
        'status_filtro': status_filtro
    })


def novo_aluno_turma(request, turma_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    turma = get_object_or_404(Turma, id=turma_id)
    
    if request.method == 'POST':
        form = AlunoForm(request.POST)
        if form.is_valid():
            aluno = form.save()
            Matricula.objects.create(aluno=aluno, nucleo=turma.nucleo, curso=turma.curso, turma=turma)
            messages.success(request, f"Aluno matriculado com sucesso na turma {turma.nome}!")
            return redirect('alunos_turma', turma_id=turma.id)
    else:
        form = AlunoForm()
        
    return render(request, 'aluno_form.html', {'form': form, 'nucleo': turma.nucleo, 'curso': turma.curso, 'turma': turma})

def novo_aluno_experimental_turma(request, turma_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    turma = get_object_or_404(Turma, id=turma_id)
    
    if request.method == 'POST':
        form = AlunoExperimentalForm(request.POST)
        if form.is_valid():
            aluno = form.save(commit=False)
            aluno.nucleo = turma.nucleo
            aluno.curso = turma.curso
            aluno.save()
            messages.success(request, f"Aula experimental registrada com sucesso na turma {turma.nome}!")
            return redirect('alunos_turma', turma_id=turma.id)
    else:
        form = AlunoExperimentalForm()
        
    return render(request, 'experimental_form.html', {'form': form, 'nucleo': turma.nucleo, 'curso': turma.curso, 'turma': turma})


def alternar_status_aluno(request, matricula_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    matricula = get_object_or_404(Matricula, id=matricula_id)
    
    if request.method == 'POST':
        # Inverte o status
        matricula.ativo = not matricula.ativo
        matricula.save()
        
        status_texto = "ativado" if matricula.ativo else "desligado"
        messages.success(request, f"Aluno {matricula.aluno.nome} {status_texto} com sucesso!")
        
        if matricula.turma:
            return redirect('alunos_turma', turma_id=matricula.turma.id)
        return redirect('dashboard')
        
    # Se for GET, exibe a tela de confirmacao
    return render(request, 'confirmar_status_aluno.html', {'matricula': matricula})
