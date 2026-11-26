from django.db import models
import uuid
from presentia.churches.models import Igreja

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

class Curso(BaseModel):
    nome = models.CharField(max_length=100, unique=True)
    ordem = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        db_table = "tb_cursos"
        ordering = ["ordem"]

    def __str__(self) -> str:
        return f"{self.ordem}o - {self.nome}"

class Nucleo(BaseModel):
    nome = models.CharField(max_length=150)
    igreja = models.ForeignKey(Igreja, on_delete=models.PROTECT, related_name="nucleos")

    class Meta:
        db_table = "tb_nucleos"
        ordering = ["nome"]

    def __str__(self) -> str:
        return f"{self.nome} - {self.igreja.nome}"

class Turma(BaseModel):
    nome = models.CharField(max_length=100)
    nucleo = models.ForeignKey(Nucleo, on_delete=models.CASCADE, related_name="turmas")
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="turmas")
    data_inicio = models.DateField()
    data_fim = models.DateField()

    class Meta:
        db_table = "tb_turmas"
        ordering = ["-data_inicio"]

    def __str__(self) -> str:
        return f"{self.nome} ({self.curso.nome})"

class Aula(BaseModel):
    nucleo = models.ForeignKey(Nucleo, on_delete=models.CASCADE, related_name="aulas")
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="aulas", null=True, blank=True)
    turma = models.ForeignKey(Turma, on_delete=models.SET_NULL, related_name="aulas", null=True, blank=True)
    data = models.DateField()
    topico = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "tb_aulas"
        ordering = ["-data"]

    def __str__(self) -> str:
        return f"{self.nucleo.nome} - {self.data}"
