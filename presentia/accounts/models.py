from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import uuid

class Usuario(models.Model):
    nome_completo = models.CharField(max_length=150)
    login = models.CharField(max_length=50, unique=True)
    senha_hash = models.CharField(max_length=255)
    email = models.EmailField(max_length=100, unique=True)
    telefone = models.CharField(max_length=15)
    is_admin = models.BooleanField(default=False)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_usuarios'

    def set_senha(self, senha_limpa):
        self.senha_hash = make_password(senha_limpa)

    def check_senha(self, senha_limpa):
        return check_password(senha_limpa, self.senha_hash)

    def __str__(self):
        return self.nome_completo

class SolicitacaoAcesso(models.Model):
    nome_completo = models.CharField(max_length=150)
    login = models.CharField(max_length=50, unique=True)
    senha_hash = models.CharField(max_length=255)
    email = models.EmailField(max_length=100, unique=True)
    telefone = models.CharField(max_length=15)
    status = models.CharField(max_length=20, default='pendente')
    data_solicitacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_solicitacoes_acesso'

    def __str__(self):
        return self.nome_completo

class Aluno(models.Model):
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=11)
    email = models.EmailField(max_length=100, unique=True)
    data_inicio = models.DateField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_alunos'
        ordering = ["nome"]

    def __str__(self):
        return self.nome


