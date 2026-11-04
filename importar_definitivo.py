import os
import django
import csv
import re
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from presentia.accounts.models import Aluno
from presentia.courses.models import Nucleo, Aula
from presentia.attendance.models import Matricula, Frequencia

print("Iniciando importação definitiva da planilha...")

try:
    nucleo = Nucleo.objects.get(nome__icontains="FVC IPAN")
except Nucleo.DoesNotExist:
    print("ERRO: Núcleo 'FVC IPAN' não encontrado.")
    exit()

with open('frequencia.csv', mode='r', encoding='utf-8-sig') as f:
    leitor = csv.reader(f, delimiter=',')
    
    # Pula as 4 primeiras linhas
    for _ in range(4):
        next(leitor)
        
    cabecalhos = next(leitor)
    
    # Regex para achar as colunas de data (formato DD/MM)
    colunas_datas = []
    padrao_data = re.compile(r'(\d{1,2})/(\d{2})')
    
    for i, col in enumerate(cabecalhos):
        col_limpa = col.strip()
        match = padrao_data.search(col_limpa)
        if match:
            dia, mes = match.groups()
            try:
                data_obj = datetime(int('2026'), int(mes), int(dia)).date()
                colunas_datas.append((i, data_obj))
            except ValueError:
                pass
                
    print(f"Encontradas {len(colunas_datas)} datas de aula na planilha.")

    # Cria as Aulas
    aulas_dict = {}
    for _, data_aula in colunas_datas:
        aula, _ = Aula.objects.get_or_create(
            nucleo=nucleo,
            data=data_aula,
            defaults={'topico': 'Aula Importada'}
        )
        aulas_dict[data_aula] = aula

    alunos_importados = 0
    frequencias_importadas = 0
    
    for linha in leitor:
        if not linha or len(linha) < 8:
            continue
            
        nome = linha[1].strip()
        if not nome or nome == "Nome" or "CANCELADOS" in nome:
            continue
            
        telefone = linha[2].strip().replace(" ", "").replace("-", "")
        email = linha[3].strip()
        data_matricula_str = linha[6].strip()
        
        try:
            if '/' in data_matricula_str:
                data_matricula = datetime.strptime(data_matricula_str, "%d/%m/%Y").date()
            else:
                data_matricula = datetime(2026, 1, 1).date()
        except ValueError:
            data_matricula = datetime(2026, 1, 1).date()

        aluno, criado = Aluno.objects.get_or_create(
            email=email,
            defaults={
                'nome': nome,
                'telefone': telefone if telefone else '00000000000',
                'data_inicio': data_matricula
            }
        )
        if criado:
            alunos_importados += 1

        matricula, _ = Matricula.objects.get_or_create(aluno=aluno, nucleo=nucleo)

        for index_col, data_aula in colunas_datas:
            if index_col < len(linha):
                valor = linha[index_col].strip().upper()
                
                if valor == 'P':
                    status = Frequencia.Status.PRESENTE
                elif valor == 'F':
                    status = Frequencia.Status.AUSENTE
                else:
                    continue
                
                aula = aulas_dict[data_aula]
                _, freq_criada = Frequencia.objects.get_or_create(
                    aula=aula,
                    matricula=matricula,
                    defaults={'status': status}
                )
                if freq_criada:
                    frequencias_importadas += 1

print(f"✅ Importação concluída!")
print(f"Alunos cadastrados: {alunos_importados}")
print(f"Total de presenças/faltas importadas: {frequencias_importadas}")


