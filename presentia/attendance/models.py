from django.db import models
import uuid
from presentia.courses.models import Aula, Nucleo, Curso, Turma
from presentia.accounts.models import Aluno

class Matricula(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="matriculas")
    nucleo = models.ForeignKey(Nucleo, on_delete=models.CASCADE, related_name="matriculas", null=True, blank=True)
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="matriculas", null=True, blank=True)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name="matriculas", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    status_pagamento = models.CharField(max_length=20, default='Em dia')

    class Meta:
        db_table = 'tb_matriculas'
        # Removemos a constraint antiga e deixamos o banco gerenciar a unicidade por turma se necessario
        # constraints = [
        #     models.UniqueConstraint(fields=["aluno", "turma"], name="idx_unique_aluno_turma")
        # ]

    def __str__(self) -> str:
        return f"{self.aluno.nome} na turma {self.turma.nome if self.turma else 'Sem Turma'}"

class Frequencia(models.Model):
    class Status(models.TextChoices):
        PRESENTE = "presente", "Presente"
        AUSENTE = "ausente", "Ausente"
        JUSTIFICADA = "justificada", "Falta Justificada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name="frequencias")
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name="frequencias")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENTE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tb_frequencias'
        constraints = [
            models.UniqueConstraint(fields=["aula", "matricula"], name="idx_unique_aula_matricula")
        ]

    def __str__(self) -> str:
        return f"{self.matricula.aluno.nome} - {self.aula.data}: {self.get_status_display()}"

class AlunoExperimental(models.Model):
    id = models.AutoField(primary_key=True)
    nome_completo = models.CharField(max_length=150)
    celular = models.CharField(max_length=11, unique=True)
    data_visita = models.DateTimeField(auto_now_add=True)
    nucleo = models.ForeignKey(Nucleo, on_delete=models.CASCADE, related_name="experimentais")
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="experimentais", null=True, blank=True)

    class Meta:
        db_table = "tb_alunos_experimentais"
        ordering = ["-data_visita"]

    def __str__(self) -> str:
        return f"{self.nome_completo} - {self.celular}"


class Mensalidade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name='mensalidades')
    numero_mes = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20)
    data_status = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_mensalidades'
        constraints = [
            models.UniqueConstraint(fields=['matricula', 'numero_mes'], name='idx_unique_matricula_mes')
        ]

    def __str__(self):
        return f"{self.matricula.aluno.nome} - Mes {self.numero_mes}: {self.status}"
