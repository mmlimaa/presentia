from django.urls import path
from presentia.accounts.views import (
    login_view, logout_view, SolicitacaoAcessoView, 
    alunos_nucleo, novo_aluno_nucleo, novo_aluno_experimental, editar_aluno,
    gerenciar_solicitacoes, aprovar_solicitacao, recusar_solicitacao,
    gerenciar_usuarios, novo_usuario, resetar_senha, alternar_admin, excluir_usuario, editar_usuario,
    alunos_turma, novo_aluno_turma, novo_aluno_experimental_turma, 
    frequencia_turma, copiar_alunos_turma, processar_copia_alunos,
    alternar_status_aluno, selecionar_turma_chamada
)
from presentia.churches.views import lista_igrejas, nova_igreja, editar_igreja, excluir_igreja
from presentia.courses.views import (
    lista_nucleos, novo_nucleo, lista_turmas, nova_turma, 
    editar_turma, excluir_turma, api_contar_turmas
)
from presentia.attendance.views import (
    dashboard_view, chamada_nucleo, lista_frequencia, consulta_frequencia,
    importar_planilha_financeira, api_mensalidades_aluno,
    relatorio_frequencia_aulas
)

urlpatterns = [
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('solicitar-acesso/', SolicitacaoAcessoView.as_view(), name='solicitar_acesso'),
    
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Igrejas
    path('igrejas/', lista_igrejas, name='igrejas_lista'),
    path('igrejas/nova/', nova_igreja, name='igreja_nova'),
    path('igrejas/<uuid:igreja_id>/editar/', editar_igreja, name='editar_igreja'),
    path('igrejas/<uuid:igreja_id>/excluir/', excluir_igreja, name='excluir_igreja'),
    
    # Nucleos
    path('nucleos/', lista_nucleos, name='nucleos_lista'),
    path('nucleos/novo/', novo_nucleo, name='nucleo_novo'),
    path('nucleos/<uuid:nucleo_id>/alunos/', alunos_nucleo, name='alunos_nucleo'),
    path('nucleos/<uuid:nucleo_id>/alunos/novo/', novo_aluno_nucleo, name='novo_aluno_nucleo'),
    path('nucleos/<uuid:nucleo_id>/experimental/', novo_aluno_experimental, name='novo_aluno_experimental'),
    path('api/nucleos/<uuid:nucleo_id>/turmas/', api_contar_turmas, name='api_contar_turmas'),
    
    # Turmas
    path('turmas/', lista_turmas, name='turmas_lista'),
    path('turmas/nova/', nova_turma, name='turma_nova'),
    path('turmas/<uuid:turma_id>/editar/', editar_turma, name='editar_turma'),
    path('turmas/<uuid:turma_id>/excluir/', excluir_turma, name='excluir_turma'),
    path('turmas/<uuid:turma_id>/alunos/', alunos_turma, name='alunos_turma'),
    path('turmas/<uuid:turma_id>/alunos/novo/', novo_aluno_turma, name='novo_aluno_turma'),
    path('turmas/<uuid:turma_id>/experimental/', novo_aluno_experimental_turma, name='novo_aluno_experimental_turma'),
    path('turmas/<uuid:turma_id>/frequencia/', frequencia_turma, name='frequencia_turma'),
    path('turmas/<uuid:turma_id>/copiar/', copiar_alunos_turma, name='copiar_alunos_turma'),
    path('turmas/<uuid:turma_id>/copiar/processar/', processar_copia_alunos, name='processar_copia_alunos'),
    
    # Chamada
    path('chamada/', selecionar_turma_chamada, name='selecionar_turma_chamada'),
    path('nucleos/<uuid:nucleo_id>/chamada/', chamada_nucleo, name='chamada_nucleo'),
    
    # Alunos
    path('alunos/<int:aluno_id>/editar/', editar_aluno, name='editar_aluno'),
    path('matriculas/<uuid:matricula_id>/status/', alternar_status_aluno, name='alternar_status_aluno'),
    
    # Solicitacoes e Usuarios
    path('solicitacoes/', gerenciar_solicitacoes, name='gerenciar_solicitacoes'),
    path('solicitacoes/<int:solicitacao_id>/aprovar/', aprovar_solicitacao, name='aprovar_solicitacao'),
    path('solicitacoes/<int:solicitacao_id>/recusar/', recusar_solicitacao, name='recusar_solicitacao'),
    path('usuarios/', gerenciar_usuarios, name='gerenciar_usuarios'),
    path('usuarios/novo/', novo_usuario, name='novo_usuario'),
    path('usuarios/<int:usuario_id>/editar/', editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/resetar-senha/', resetar_senha, name='resetar_senha'),
    path('usuarios/<int:usuario_id>/alternar-admin/', alternar_admin, name='alternar_admin'),
    path('usuarios/<int:usuario_id>/excluir/', excluir_usuario, name='excluir_usuario'),
    
    # Financeiro
    path('financeiro/importar/', importar_planilha_financeira, name='importar_planilha_financeira'),
    path('api/mensalidades/<uuid:matricula_id>/', api_mensalidades_aluno, name='api_mensalidades_aluno'),
    
    # Frequencia e Relatorios
    path('frequencia/', lista_frequencia, name='frequencia_lista'),
    path('frequencia/consultas/', consulta_frequencia, name='consulta_frequencia'),
    path('frequencia/relatorio-aulas/', relatorio_frequencia_aulas, name='relatorio_frequencia_aulas'),
]
