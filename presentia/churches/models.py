from django.db import models
import uuid

class Igreja(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=150)
    cidade = models.CharField(max_length=100)
    endereco = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tb_igrejas'
        ordering = ["nome"]

    def __str__(self) -> str:
        return f"{self.nome} ({self.cidade})"


