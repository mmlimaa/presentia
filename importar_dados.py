import os
import django
import csv
from datetime import datetime
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from presentia.accounts.models import Aluno
from presentia.courses.models import Nucleo, Aula
from presentia.attendance.models import Matricula, Frequencia
from presentia.churches.models import Igreja

print("Iniciando importação da planilha...")

# 1. Busca o núcleo e a igreja (assumindo que já foram criados)
try:
    nucleo = Nucleo.objects.get(nome__icontains="FVC IPAN")
    print(f"Núcleo encontrado: {nucleo.nome}")
except Nucleo.DoesNotExist:
    print("ERRO: Núcleo 'FVC IPAN' não encontrado. Crie ele antes de importar.")
    exit()

# 2. Abre o arquivo CSV
with open('frequencia.csv', mode='r', encoding='utf-8-sig') as f:
    leitor = csv.reader(f, delimiter=',')
    
    # Pula as 4 primeiras linhas (cabeçalho do Excel)
    for _ in range(4):
        next(leitor)
        
    # A quinta linha tem os cabeçalhos das colunas
    cabecalhos = next(leitor)
    
    # Pega os nomes das colunas de datas (a partir do índice 8)
    colunas_datas = cabecalhos[8:]
    
    # Filtra apenas as datas válidas no formato DD/MM
    datas_validas = []
    for i, col in enumerate(colunas_datas):
        col_limpa = col.strip()
        if '/' in col_limpa:
            # Assumimos o ano de 2026 para toda a planilha
            try:
                data_obj = datetime.strptime(f"{col_limpa}/2026", "%d/%m/%Y").date()
                datas_validas.append((8 + i, data_obj)) # Guarda a posição e a data
            except ValueError:
                pass # Ignora colunas que não são datas exatas
    
    print(f"Encontradas {len(datas_validas)} datas de aula na planilha.")

    # 3. Cria as Aulas no banco para cada data
    aulas_dict = {}
    for _, data_aula in datas_validas:
        aula, criada = Aula.objects.get_or_create(
            nucleo=nucleo,
            data=data_aula,
            defaults={'topico': 'Aula Importada'}
        )
        aulas_dict[data_aula] = aula

    # 4. Processa cada linha de aluno
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
        
        # Converte a data de matrícula
        try:
            if '/' in data_matricula_str:
                data_matricula = datetime.strptime(data_matricula_str, "%d/%m/%Y").date()
            else:
                data_matricula = datetime(2026, 1, 1).date()
        except ValueError:
            data_matricula = datetime(2026, 1, 1).date()

        # Cria ou atualiza o Aluno
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

        # Cria a Matrícula (se não existir)
        matricula, mat_criada = Matricula.objects.get_or_create(
            aluno=aluno,
            nucleo=nucleo
        )

        # 5. Lança as frequências
        for index_col, data_aula in datas_validas:
            if index_col < len(linha):
                valor = linha[index_col].strip().upper()
                
                # P = Presente, F = Falta (Ausente)
                if valor == 'P':
                    status = Frequencia.Status.PRESENTE
                elif valor == 'F':
                    status = Frequencia.Status.AUSENTE
                else:
                    continue # Se estiver vazio, ignora
                
                aula = aulas_dict[data_aula]
                _, freq_criada = Frequencia.objects.get_or_create(
                    aula=aula,
                    matricula=matricula,
                    defaults={'status': status}
                )
                if freq_criada:
                    frequencias_importadas += 1

print(f"✅ Importação concluída com sucesso!")
print(f"Alunos novos cadastrados: {alunos_importados}")
print(f"Total de presenças/faltas importadas: {frequencias_importadas}")


