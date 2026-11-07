from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime, date
import calendar

from .models import Frequencia, Matricula, AlunoExperimental
from presentia.courses.models import Nucleo, Aula, Turma, Curso
from presentia.churches.models import Igreja
from presentia.accounts.models import Aluno

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- DASHBOARD ---
def dashboard_view(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    from presentia.accounts.models import Aluno
    from presentia.courses.models import Nucleo
    from django.db.models import Count
    
    total_alunos = Aluno.objects.count()
    total_nucleos = Nucleo.objects.count()
    total_aulas = Aula.objects.count()
    
    # Busca as 5 ultimas aulas que TEM turma associada E TEM frequencias
    ultimas_aulas = Aula.objects.filter(
        turma__isnull=False,
        frequencias__isnull=False
    ).annotate(
        num_freq=Count('frequencias')
    ).select_related('turma', 'turma__curso', 'nucleo').order_by('-data', '-created_at')[:5]
    
    contexto = {
        'total_alunos': total_alunos,
        'total_nucleos': total_nucleos,
        'total_aulas': total_aulas,
        'ultimas_aulas': ultimas_aulas,
    }
    
    return render(request, 'dashboard.html', contexto)


def lista_frequencia(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    from django.db import connection
    from presentia.churches.models import Igreja
    from presentia.courses.models import Nucleo
    
    # Filtros
    igreja_id = request.GET.get('igreja')
    nucleo_id = request.GET.get('nucleo')
    
    igrejas = Igreja.objects.all().order_by('nome')
    nucleos = Nucleo.objects.all().order_by('nome')
    
    if igreja_id:
        nucleos = nucleos.filter(igreja_id=igreja_id)
        
    turmas_dados = []
    
    # Se um nucleo foi selecionado, busca as turmas
    if nucleo_id:
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
            
            # Conta alunos ativos, inativos e experimentais
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM tb_matriculas WHERE turma_id = %s::uuid AND ativo = true", [turma_id])
                ativos = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM tb_matriculas WHERE turma_id = %s::uuid AND ativo = false", [turma_id])
                inativos = cursor.fetchone()[0]
                
                # Pega o nucleo_id e curso_id da turma para contar os experimentais
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

    # 1. Busca ou cria a Aula EXATAMENTE pela Turma, Data e Núcleo
    aula, created = Aula.objects.get_or_create(
        nucleo=nucleo,
        turma=turma,
        data=data_aula,
        defaults={'topico': 'Aula Regular', 'curso': turma.curso}
    )
    
    # 2. Busca as frequencias existentes
    frequencias = Frequencia.objects.filter(aula=aula).select_related('matricula__aluno')
    
    # 3. Se nao existirem (primeira vez nesta data), cria apenas para alunos ativos
    if not frequencias.exists():
        matriculas_ativas = Matricula.objects.filter(turma=turma, ativo=True)
        novas_frequencias = []
        for mat in matriculas_ativas:
            novas_frequencias.append(
                Frequencia(aula=aula, matricula=mat, status=Frequencia.Status.AUSENTE)
            )
        Frequencia.objects.bulk_create(novas_frequencias)
        frequencias = Frequencia.objects.filter(aula=aula).select_related('matricula__aluno')

    # 4. Salva as alteracoes (POST)
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

            # Busca todas as frequencias no periodo da turma
            frequencias = Frequencia.objects.filter(
                aula__turma=turma,
                aula__data__gte=data_inicio,
                aula__data__lte=data_fim
            ).select_related('matricula__aluno', 'aula').order_by('aula__data', 'matricula__aluno__nome')

            if aluno_nome:
                frequencias = frequencias.filter(matricula__aluno__nome__icontains=aluno_nome)

            # Agrupa por mes
            agrupado = {}
            for f in frequencias:
                mes_ano = f.aula.data.strftime('%Y-%m')
                dia = f.aula.data.day
                nome = f.matricula.aluno.nome
                
                if mes_ano not in agrupado:
                    agrupado[mes_ano] = {}
                if nome not in agrupado[mes_ano]:
                    agrupado[mes_ano][nome] = {}
                
                agrupado[mes_ano][nome][dia] = f.status

            meses_pt = {'01': 'JAN', '02': 'FEV', '03': 'MAR', '04': 'ABR', '05': 'MAI', '06': 'JUN',
                        '07': 'JUL', '08': 'AGO', '09': 'SET', '10': 'OUT', '11': 'NOV', '12': 'DEZ'}

            blocos = []
            for mes in sorted(agrupado.keys()):
                # Pega todos os dias que tiveram aula naquele mes
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
                        status = agrupado[mes][nome].get(dia)
                        
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
        
        # Cabecalho: Aluno + dias
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




from presentia.courses.models import Turma

