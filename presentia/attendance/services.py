from django.db import transaction
from presentia.courses.models import Aula
from presentia.attendance.models import Matricula, Frequencia

@transaction.atomic
def gerar_frequencia_em_lote(aula: Aula) -> None:
    """
    Gera os registros de frequencia para todos os alunos matriculados no nucleo da aula.
    Define o status inicial como AUSENTE.
    """
    matriculas = Matricula.objects.filter(nucleo=aula.nucleo)
    frequencias_existentes = Frequencia.objects.filter(aula=aula).values_list('matricula_id', flat=True)
    
    novas_frequencias = []
    for matricula in matriculas:
        if matricula.id not in frequencias_existentes:
            novas_frequencias.append(
                Frequencia(
                    aula=aula,
                    matricula=matricula,
                    status=Frequencia.Status.AUSENTE
                )
            )
            
    if novas_frequencias:
        Frequencia.objects.bulk_create(novas_frequencias)


