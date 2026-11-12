from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from datetime import datetime, date
import calendar
import csv
import io
import re

from .models import Frequencia, Matricula, AlunoExperimental, Mensalidade
from presentia.courses.models import Nucleo, Aula, Curso, Turma
from presentia.churches.models import Igreja
from presentia.accounts.models import Aluno

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4, portrait
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- DASHBOARD ---
def dashboard_view(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    total_alunos = Aluno.objects.count()
    total_nucleos = Nucleo.objects.count()
    total_aulas = Aula.objects.count()
    
    ultimas_aulas = Aula.objects.filter(
        turma__isnull=False,
        frequencias__isnull=False
    ).distinct().select_related('turma', 'turma__curso', 'nucleo').order_by('-data', '-created_at')[:5]
    
    contexto = {
        'total_alunos': total_alunos,
        'total_nucleos': total_nucleos,
        'total_aulas': total_aulas,
        'ultimas_aulas': ultimas_aulas,
    }
    return render(request, 'dashboard.html', contexto)

# --- FREQUENCIA ---
def lista_frequencia(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    from presentia.churches.models import Igreja
    from presentia.courses.models import Nucleo
    
    igreja_id = request.GET.get('igreja')
    nucleo_id = request.GET.get('nucleo')
    
    igrejas = Igreja.objects.all().order_by('nome')
    nucleos = Nucleo.objects.all().order_by('nome')
    
    if igreja_id:
        nucleos = nucleos.filter(igreja_id=igreja_id)
        
    turmas_dados = []
    
    if nucleo_id:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT t.id, t.nome, t.data_inicio, t.data_fim, c.nome as curso_nome
                FROM tb_turmas t
                JOIN tb_cursos c ON c.id = t.curso_id
                WHERE t.nucleo_id = %s::uuid
                ORDER BY t.data_inicio DESC
            ''', [nucleo_id])
            rows = cursor.fetchall()
            
        for row in rows:
            turma_id = str(row[0])
            turma_nome = row[1]
            data_inicio = row[2]
            data_fim = row[3]
            curso_nome = row[4]
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM tb_matriculas WHERE turma_id = %s::uuid AND ativo = true", [turma_id])
                ativos = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM tb_matriculas WHERE turma_id = %s::uuid AND ativo = false", [turma_id])
                inativos = cursor.fetchone()[0]
                
                cursor.execute("SELECT nucleo_id, curso_id FROM tb_turmas WHERE id = %s::uuid", [turma_id])
                turma_nucleo_id, turma_curso_id = cursor.fetchone()
                
                cursor.execute("SELECT COUNT(*) FROM tb_alunos_experimentais WHERE nucleo_id = %s::uuid AND curso_id = %s::uuid", [str(turma_nucleo_id), str(turma_curso_id)])
                experimentais = cursor.fetchone()[0]
                
            turmas_dados.append({
                'id': turma_id,
                'nome': turma_nome,
                'curso': curso_nome,
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'ativos': ativos,
                'inativos': inativos,
                'experimentais': experimentais
            })
            
    return render(request, 'frequencia_lista.html', {
        'igrejas': igrejas,
        'nucleos': nucleos,
        'turmas': turmas_dados,
        'igreja_id': igreja_id,
        'nucleo_id': nucleo_id
    })

def chamada_nucleo(request, nucleo_id):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    nucleo = get_object_or_404(Nucleo, id=nucleo_id)
    turma_id = request.GET.get('turma')
    
    if not turma_id:
        messages.error(request, "Selecione uma turma.")
        return redirect('frequencia_lista')
        
    turma = get_object_or_404(Turma, id=turma_id)
    
    data_str = request.GET.get('data')
    if not data_str:
        data_str = datetime.today().strftime('%Y-%m-%d')
    
    data_aula = datetime.strptime(data_str, '%Y-%m-%d').date()

    aula, created = Aula.objects.get_or_create(
        nucleo=nucleo,
        data=data_aula,
        turma=turma,
        defaults={'topico': 'Aula Regular', 'curso': turma.curso}
    )
    
    frequencias = Frequencia.objects.filter(aula=aula).select_related('matricula__aluno')
    
    if not frequencias.exists():
        matriculas_ativas = Matricula.objects.filter(turma=turma, ativo=True)
        novas_frequencias = [
            Frequencia(aula=aula, matricula=mat, status=Frequencia.Status.AUSENTE) 
            for mat in matriculas_ativas
        ]
        Frequencia.objects.bulk_create(novas_frequencias)
        frequencias = Frequencia.objects.filter(aula=aula).select_related('matricula__aluno')

    if request.method == 'POST':
        for freq in frequencias:
            novo_status = request.POST.get(f'status_{freq.id}')
            if novo_status in [Frequencia.Status.PRESENTE, Frequencia.Status.AUSENTE, Frequencia.Status.JUSTIFICADA]:
                freq.status = novo_status
                freq.save()
        messages.success(request, "Chamada salva com sucesso!")
        return redirect(f"{request.path}?data={data_str}&turma={turma_id}")

    experimentais = AlunoExperimental.objects.filter(nucleo=nucleo, curso=turma.curso, data_visita__date=data_aula)
    
    return render(request, 'chamada.html', {
        'nucleo': nucleo,
        'turma': turma,
        'aula': aula,
        'frequencias': frequencias,
        'experimentais': experimentais,
        'data_str': data_str,
    })

# --- RELATORIOS ---
def consulta_frequencia(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    from presentia.churches.models import Igreja
    from presentia.courses.models import Nucleo, Turma
    
    igrejas = Igreja.objects.all().order_by('nome')
    nucleos = Nucleo.objects.all().order_by('nome')
    
    igreja_id = request.GET.get('igreja')
    nucleo_id = request.GET.get('nucleo')
    turma_id = request.GET.get('turma')
    aluno_nome = request.GET.get('aluno_nome')
    
    if igreja_id:
        nucleos = nucleos.filter(igreja_id=igreja_id)
        
    turmas = Turma.objects.none()
    if nucleo_id:
        turmas = Turma.objects.filter(nucleo_id=nucleo_id).order_by('-data_inicio')

    contexto = {
        'igrejas': igrejas, 
        'nucleos': nucleos, 
        'turmas': turmas,
        'igreja_id': igreja_id, 
        'nucleo_id': nucleo_id,
        'turma_id': turma_id,
        'aluno_nome': aluno_nome,
    }

    if turma_id:
        try:
            turma = get_object_or_404(Turma, id=turma_id)
            data_inicio = turma.data_inicio
            data_fim = turma.data_fim

            frequencias = Frequencia.objects.filter(
                aula__turma=turma,
                aula__data__gte=data_inicio,
                aula__data__lte=data_fim
            ).select_related('matricula__aluno', 'aula')

            if aluno_nome:
                frequencias = frequencias.filter(matricula__aluno__nome__icontains=aluno_nome)

            agrupado = {}
            for f in frequencias:
                mes_ano = f.aula.data.strftime('%Y-%m')
                nome = f.matricula.aluno.nome
                data_str = f.aula.data.strftime('%Y-%m-%d')
                
                if mes_ano not in agrupado:
                    agrupado[mes_ano] = {}
                if nome not in agrupado[mes_ano]:
                    agrupado[mes_ano][nome] = {}
                
                agrupado[mes_ano][nome][data_str] = f.status

            meses_pt = {'01': 'JAN', '02': 'FEV', '03': 'MAR', '04': 'ABR', '05': 'MAI', '06': 'JUN',
                        '07': 'JUL', '08': 'AGO', '09': 'SET', '10': 'OUT', '11': 'NOV', '12': 'DEZ'}

            blocos = []
            for mes in sorted(agrupado.keys()):
                aulas_mes = Aula.objects.filter(
                    turma=turma, 
                    data__year=int(mes.split('-')[0]), 
                    data__month=int(mes.split('-')[1])
                ).order_by('data')
                dias_do_mes = [a.data.day for a in aulas_mes]

                ano_mes = mes.split('-')
                mes_formatado = f"{meses_pt[ano_mes[1]]}/{ano_mes[0]}"

                alunos_do_mes = []
                for nome in sorted(agrupado[mes].keys()):
                    aluno_linha = {'nome': nome, 'dias': []}
                    for dia in dias_do_mes:
                        chave_data = f"{mes}-{dia:02d}"
                        status = agrupado[mes][nome].get(chave_data)
                        
                        if status == 'presente':
                            aluno_linha['dias'].append({'dia': dia, 'status': 'P', 'cor': 'text-green-600'})
                        elif status == 'ausente':
                            aluno_linha['dias'].append({'dia': dia, 'status': 'A', 'cor': 'text-red-600'})
                        elif status == 'justificada':
                            aluno_linha['dias'].append({'dia': dia, 'status': 'J', 'cor': 'text-black'})
                        else:
                            aluno_linha['dias'].append({'dia': dia, 'status': '-', 'cor': 'text-gray-400'})
                    
                    alunos_do_mes.append(aluno_linha)
                
                blocos.append({
                    'mes_ano': mes_formatado,
                    'dias': dias_do_mes,
                    'alunos': alunos_do_mes
                })

            contexto.update({
                'turma': turma,
                'blocos': blocos, 
                'gerado': True,
                'data_ini_formatada': data_inicio.strftime('%d/%m/%Y'),
                'data_fim_formatada': data_fim.strftime('%d/%m/%Y')
            })
        except Exception as e:
            messages.error(request, f"Erro no relatório: {e}")

    if request.GET.get('export') == 'pdf' and contexto.get('gerado'):
        return gerar_pdf_relatorio(contexto)

    return render(request, 'consulta_frequencia.html', contexto)

def gerar_pdf_relatorio(contexto):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_{contexto["turma"].nome}.pdf"'
    
    page_width = landscape(A4)[0] - 60
    doc = SimpleDocTemplate(response, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], alignment=1)
    sub_style = ParagraphStyle(name='SubStyle', parent=styles['Normal'], alignment=1)
    
    elements.append(Paragraph("Lista de Presença - Extrato mensal", title_style))
    elements.append(Paragraph(f"Turma: {contexto['turma'].nome} - {contexto['turma'].curso.nome}", sub_style))
    elements.append(Paragraph(f"Período: {contexto['data_ini_formatada']} a {contexto['data_fim_formatada']}", sub_style))
    elements.append(Spacer(1, 20))

    for bloco in contexto['blocos']:
        elements.append(Paragraph(f"Mês/Ano: {bloco['mes_ano']}", ParagraphStyle(name='MesStyle', parent=styles['Heading2'])))
        elements.append(Spacer(1, 10))
        
        header = ["Aluno"] + [str(d) for d in bloco['dias']]
        data = [header]
        
        for aluno in bloco['alunos']:
            row = [aluno['nome']] + [d['status'] for d in aluno['dias']]
            data.append(row)
            
        table = Table(data, repeatRows=1)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        for r_idx, aluno in enumerate(bloco['alunos'], start=1):
            for c_idx, dia in enumerate(aluno['dias'], start=1):
                if dia['status'] == 'P':
                    style.add('TEXTCOLOR', (c_idx, r_idx), (c_idx, r_idx), colors.green)
                elif dia['status'] == 'A':
                    style.add('TEXTCOLOR', (c_idx, r_idx), (c_idx, r_idx), colors.red)
                elif dia['status'] == 'J':
                    style.add('TEXTCOLOR', (c_idx, r_idx), (c_idx, r_idx), colors.black)
                    
        table.setStyle(style)
        elements.append(table)
        elements.append(Spacer(1, 30))
    
    doc.build(elements)
    return response

# --- IMPORTACAO FINANCEIRA ---
def importar_planilha_financeira(request):
    if not request.session.get('usuario_id') or not request.session.get('usuario_is_admin'):
        return redirect('login')
    
    turmas = Turma.objects.all().order_by('-data_inicio')

    if request.method == 'POST':
        turma_id = request.POST.get('turma')
        arquivo = request.FILES.get('planilha')
        
        if not turma_id or not arquivo:
            messages.error(request, "Selecione a turma e envie o arquivo CSV.")
            return redirect('importar_planilha_financeira')

        try:
            turma = Turma.objects.get(id=turma_id)
            data = arquivo.read().decode('utf-8-sig')
            leitor = csv.reader(io.StringIO(data), delimiter=',')
            linhas = list(leitor)
            
            if len(linhas) > 0 and "Nome" in linhas[0][0]:
                linhas = linhas[1:]
                
            importados = 0
            alunos_cancelados = 0
            secao_atual = 'ativo'

            for linha in linhas:
                if not linha or len(linha) < 2: 
                    continue
                
                linha_texto = " ".join(linha).upper()
                
                if "CANCELADO" in linha_texto:
                    if "CLIENTE" in linha_texto:
                        secao_atual = 'cancelado_cliente'
                    elif "INADIMPLENTE" in linha_texto:
                        secao_atual = 'cancelado_inadimplente'
                    else:
                        secao_atual = 'cancelado_generico'
                    continue

                email = ""
                for celula in linha:
                    if "@" in celula and "." in celula:
                        email = celula.strip().lower()
                        break
                
                if not email:
                    continue

                nome = linha[0].strip().upper() if len(linha) > 0 else "ALUNO SEM NOME"
                telefone = linha[1].strip().replace(" ", "").replace("-", "") if len(linha) > 1 else ""

                aluno, _ = Aluno.objects.get_or_create(
                    email=email, 
                    defaults={'nome': nome, 'telefone': telefone, 'data_inicio': datetime.today().date()}
                )
                
                matricula, _ = Matricula.objects.get_or_create(
                    aluno=aluno, turma=turma,
                    defaults={'nucleo': turma.nucleo, 'curso': turma.curso}
                )
                
                Mensalidade.objects.filter(matricula=matricula).delete()
                status_geral = 'Em dia'
                
                if secao_atual.startswith('cancelado'):
                    matricula.ativo = False
                    if secao_atual == 'cancelado_inadimplente':
                        status_geral = 'Inadimplente'
                    alunos_cancelados += 1
                else:
                    matricula.ativo = True
                    for i in range(4, len(linha)):
                        valor = linha[i].strip().upper()
                        if not valor: continue
                        numero_mes = i - 3
                        
                        if 'PAGO' in valor:
                            status = 'PAGO'
                        elif 'INADIMPLENTE' in valor:
                            status = 'INADIMPLENTE'
                            status_geral = 'Inadimplente'
                        else:
                            continue
                            
                        data_status = None
                        match = re.search(r'(\d{2}/\d{2}/\d{4})', valor)
                        if match:
                            try:
                                data_status = datetime.strptime(match.group(1), '%d/%m/%Y').date()
                            except ValueError:
                                pass
                        
                        Mensalidade.objects.create(
                            matricula=matricula,
                            numero_mes=numero_mes,
                            status=status,
                            data_status=data_status
                        )
                    
                    if not Mensalidade.objects.filter(matricula=matricula).exists():
                        status_geral = 'Quitado'

                matricula.status_pagamento = status_geral
                matricula.save()
                importados += 1

            messages.success(request, f"{importados} alunos processados ({alunos_cancelados} desativados).")
            return redirect('alunos_turma', turma_id=turma.id)
            
        except Exception as e:
            messages.error(request, f"Erro ao importar: {e}")
            return redirect('importar_planilha_financeira')

    return render(request, 'importar_financeiro.html', {'turmas': turmas})

def api_mensalidades_aluno(request, matricula_id):
    if not request.session.get('usuario_id'):
        return JsonResponse({'error': 'Nao autorizado'}, status=401)
        
    try:
        mensalidades = Mensalidade.objects.filter(
            matricula_id=matricula_id, 
            status='INADIMPLENTE'
        ).order_by('numero_mes')
        
        dados = []
        for m in mensalidades:
            dados.append({
                'mes': m.numero_mes,
                'status': m.status,
                'data': m.data_status.strftime('%d/%m/%Y') if m.data_status else 'Sem data'
            })
            
        return JsonResponse({'mensalidades': dados})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# --- RELATORIO DE FREQUENCIA DAS AULAS ---
def relatorio_frequencia_aulas(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    from presentia.churches.models import Igreja
    from presentia.courses.models import Nucleo, Turma
    from presentia.accounts.models import Aluno
    from presentia.attendance.models import Matricula, Frequencia, Aula
    
    igrejas = Igreja.objects.all().order_by('nome')
    
    igreja_id = request.GET.get('igreja')
    nucleo_id = request.GET.get('nucleo')
    turma_id = request.GET.get('turma')
    pagamento_filtro = request.GET.get('pagamento', 'todos')
    
    # Se nao houver igreja, apenas mostra os filtros
    if not igreja_id:
        return render(request, 'relatorio_frequencia_aulas.html', {'igrejas': igrejas, 'gerado': False})
        
    # Busca os nucleos da igreja
    nucleos = Nucleo.objects.filter(igreja_id=igreja_id).order_by('nome')
    
    # Busca as turmas do nucleo ou da igreja
    turmas = Turma.objects.none()
    if nucleo_id:
        turmas = Turma.objects.filter(nucleo_id=nucleo_id).order_by('-data_inicio')
    else:
        turmas = Turma.objects.filter(nucleo__igreja_id=igreja_id).order_by('-data_inicio')

    # Define quais turmas serao processadas
    if turma_id:
        turmas_processar = Turma.objects.filter(id=turma_id)
    elif nucleo_id:
        turmas_processar = Turma.objects.filter(nucleo_id=nucleo_id)
    else:
        turmas_processar = Turma.objects.filter(nucleo__igreja_id=igreja_id)

    # Agrupamento
    dados_agrupados = {}
    for turma in turmas_processar:
        igreja_nome = turma.nucleo.igreja.nome
        nucleo_nome = turma.nucleo.nome
        
        if igreja_nome not in dados_agrupados:
            dados_agrupados[igreja_nome] = {}
        if nucleo_nome not in dados_agrupados[igreja_nome]:
            dados_agrupados[igreja_nome][nucleo_nome] = []
            
        total_aulas = Aula.objects.filter(turma=turma).count()
        matriculas = Matricula.objects.filter(turma=turma).select_related('aluno').order_by('aluno__nome')
        
        alunos_dados = []
        total_ativos = 0
        total_desligados = 0
        
        for mat in matriculas:
            # Filtro de pagamento
            if pagamento_filtro != 'todos':
                if pagamento_filtro == 'avista' and mat.status_pagamento != 'Quitado':
                    continue
                elif pagamento_filtro == 'adimplente' and mat.status_pagamento != 'Em dia':
                    continue
                elif pagamento_filtro == 'inadimplente' and mat.status_pagamento != 'Inadimplente':
                    continue

            if mat.ativo:
                total_ativos += 1
            else:
                total_desligados += 1
                
            percentual = 0
            if total_aulas > 0 and mat.ativo:
                presencas = Frequencia.objects.filter(matricula=mat, status=Frequencia.Status.PRESENTE).count()
                percentual = int((presencas / total_aulas) * 100)
                
            status_pgto = mat.status_pagamento
            if status_pgto == 'Quitado':
                status_pgto = 'À Vista'
            elif status_pgto == 'Em dia':
                status_pgto = 'Adimplente'
                
            alunos_dados.append({
                'nome': mat.aluno.nome,
                'ativo': mat.ativo,
                'aproveitamento': percentual,
                'status_pagamento': status_pgto,
            })
        
        # So adiciona a turma se tiver alunos depois do filtro
        if alunos_dados:
            dados_agrupados[igreja_nome][nucleo_nome].append({
                'nome': turma.nome,
                'curso': turma.curso.nome,
                'total_ativos': total_ativos,
                'total_desligados': total_desligados,
                'alunos': alunos_dados
            })

    # Verifica se o usuario clicou em "Exibir" ou "Gerar PDF"
    exibir_dados = request.GET.get('exibir') == 'true' or request.GET.get('export') == 'pdf'
    
    contexto = {
        'igrejas': igrejas,
        'nucleos': nucleos,
        'turmas': turmas,
        'igreja_id': igreja_id,
        'nucleo_id': nucleo_id,
        'turma_id': turma_id,
        'pagamento_filtro': pagamento_filtro,
        'dados_agrupados': dados_agrupados if exibir_dados else {},
        'gerado': exibir_dados
    }

    if request.GET.get('export') == 'pdf' and contexto.get('gerado'):
        return gerar_pdf_relatorio_frequencia(contexto)

    return render(request, 'relatorio_frequencia_aulas.html', contexto)


def gerar_pdf_relatorio_frequencia(contexto):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio_frequencia_aulas.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=portrait(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], alignment=1)
    sub_style = ParagraphStyle(name='SubStyle', parent=styles['Normal'], alignment=1)
    
    elements.append(Paragraph("Relatório de Frequência das Aulas", title_style))
    elements.append(Paragraph("Presentia - Controle de Frequência", sub_style))
    elements.append(Spacer(1, 20))

    for igreja_nome, nucleos in contexto['dados_agrupados'].items():
        elements.append(Paragraph(f"Igreja: {igreja_nome}", ParagraphStyle(name='IgrejaStyle', parent=styles['Heading2'])))
        elements.append(Spacer(1, 10))
        
        for nucleo_nome, turmas in nucleos.items():
            elements.append(Paragraph(f"Núcleo: {nucleo_nome}", ParagraphStyle(name='NucleoStyle', parent=styles['Heading3'])))
            elements.append(Spacer(1, 10))
            
            for turma in turmas:
                elements.append(Paragraph(f"Turma: {turma['nome']} ({turma['curso']}) - Ativos: {turma['total_ativos']} | Desligados: {turma['total_desligados']}", ParagraphStyle(name='TurmaStyle', parent=styles['Normal'])))
                elements.append(Spacer(1, 5))
                
                # Tabela de Alunos
                header = ["Aluno", "Aproveitamento", "Pagamento", "Status"]
                data = [header]
                
                for aluno in turma['alunos']:
                    status = "Ativo" if aluno['ativo'] else "Desligado"
                    data.append([aluno['nome'], f"{aluno['aproveitamento']}%", aluno['status_pagamento'], status])
                    
                table = Table(data, colWidths=[250, 80, 80, 60])
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ])
                
                # Colorir aproveitamento
                for r_idx, aluno in enumerate(turma['alunos'], start=1):
                    if aluno['aproveitamento'] >= 75:
                        style.add('TEXTCOLOR', (1, r_idx), (1, r_idx), colors.green)
                    elif aluno['aproveitamento'] >= 50:
                        style.add('TEXTCOLOR', (1, r_idx), (1, r_idx), colors.orange)
                    else:
                        style.add('TEXTCOLOR', (1, r_idx), (1, r_idx), colors.red)
                        
                    # Colorir status
                    if aluno['status_pagamento'] == 'Inadimplente':
                        style.add('TEXTCOLOR', (2, r_idx), (2, r_idx), colors.red)
                        
                table.setStyle(style)
                elements.append(table)
                elements.append(Spacer(1, 20))
    
    doc.build(elements)
    return response
