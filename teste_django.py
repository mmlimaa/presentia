import os
import django
import csv
import io

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

# Cole aqui o caminho do seu arquivo CSV no computador
caminho_csv = r"C:\TMP\NucleoIPAN_ANO1.csv"

print("--- LENDO O ARQUIVO ---")
try:
    with open(caminho_csv, mode='r', encoding='utf-8-sig') as f:
        leitor = csv.reader(f, delimiter=',')
        linhas = list(leitor)
        
        print(f"Total de linhas lidas: {len(linhas)}")
        
        # Mostra as linhas 50 a 60 (onde devem estar os cancelados)
        for i in range(50, min(65, len(linhas))):
            print(f"Linha {i}: {linhas[i]}")
            
except Exception as e:
    print(f"Erro ao ler o arquivo: {e}")