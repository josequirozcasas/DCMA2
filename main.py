import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.data_processing.excel_reader import ler_arquivo_excel
from src.data_processing.s_curve import processar_dados, selecionar_feriados
from src.data_processing.indicators import calcular_indicadores, analisar_duracao, analisar_folga_curta
from src.visualizations.gantt import caminho_critico_com_gantt
from src.utils.utils import format_currency

# Configuração global
st.set_page_config(page_title="Validação DCMA", page_icon="📊", layout="wide")
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F5F7FA;
        padding: 20px;
        font-family: 'Roboto', sans-serif;
    }
    h1, h2, h3 {
        color: #0068C9;
    }
    .dataframe th, .dataframe td {
        font-size: 14px;
        text-align: center;
        padding: 12px;
        border: 1px solid #E0E0E0;
        background-color: #FFFFFF;
    }
    .dataframe th {
        background-color: #0068C9;
        color: white;
    }
    .stButton > button {
        background-color: #0068C9;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #004A8F;
    }
    .card {
        background-color: #FFFFFF;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
        padding: 20px;
        margin-bottom: 20px;
    }
    .card h4 {
        font-size: 16px;
        margin-bottom: 5px;
        color: #333;
    }
    .card p {
        font-size: 24px;
        margin: 0;
        color: #0068C9;
        font-weight: bold;
    }
    .card small {
        color: #555;
        font-weight: normal;
    }
    .scrollable-table {
        max-height: 350px;
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True
)

# Sidebar
st.sidebar.markdown(
    """
    <div class="card" style="background-color: #0068C9; color: white;">
        <h2 style="margin: 0; padding: 10px;">Configurações do Projeto</h2>
    </div>
    """, unsafe_allow_html=True
)
arquivo_excel = st.sidebar.file_uploader("📂 Carregar Arquivo Excel", type=["xlsx"], key="uploader1")
if arquivo_excel:
    st.sidebar.success("Arquivo carregado com sucesso!")
feriados_texto = st.sidebar.text_area(
    "📅 Feriados (DD/MM/YYYY)",
    placeholder="Ex.: 01/01/2025\n15/11/2025",
    help="Insira uma data por linha no formato DD/MM/YYYY."
)
agrupamento_opcao = st.sidebar.selectbox(
    "📅 Agrupamento da Curva S",
    options=["Mês", "Semana"],
    help="Selecione o período de agrupamento para a Curva S."
)
st.sidebar.markdown("### Fatores da Curva S")
s30 = st.sidebar.number_input("Fator S30", min_value=0.0, max_value=10.0, value=2.5, step=0.1)
s50 = st.sidebar.number_input("Fator S50", min_value=0.0, max_value=10.0, value=2.5, step=0.1)
s70 = st.sidebar.number_input("Fator S70", min_value=0.0, max_value=10.0, value=2.5, step=0.1)
st.sidebar.markdown("### Limites de Duração (em dias)")
limite_alta = st.sidebar.number_input(
    "Alta Duração (dias)",
    min_value=0.0,
    value=30.0,
    step=1.0,
    help="Número de dias para considerar tarefas de alta duração."
)
limite_baixa = st.sidebar.number_input(
    "Baixa Duração (dias)",
    min_value=0.0,
    value=5.0,
    step=1.0,
    help="Número de dias para considerar tarefas de baixa duração."
)
st.sidebar.markdown("### Limite de Folga (em dias)")
limite_folga = st.sidebar.number_input(
    "Folga Curta (dias)",
    min_value=0.0,
    value=5.0,
    step=1.0,
    help="Número de dias para considerar tarefas com folga curta."
)

# Interface principal
st.markdown("<h1 style='text-align: center;'>Validação Cronograma DCMA</h1>", unsafe_allow_html=True)
st.divider()

if arquivo_excel is not None:
    with st.spinner("Processando arquivo Excel..."):
        df = ler_arquivo_excel(arquivo_excel)
        if df is not None:
            # Resumo do Projeto
            st.subheader("Resumo do Projeto")
            leads_pct, lags_pct, relationship_types_pct, logic_pct, data_inicio, data_termino, duracao_total = calcular_indicadores(df)
            valor_agregado = df["Custo"].sum()
            valor_agregadof = format_currency(valor_agregado)

            # Linha 1: 4 cards principais
            cols1 = st.columns(4, gap="large")
            with cols1[0]:
                st.markdown(
                    f"""
                    <div class="card">
                        <h4>📅 Início BL</h4>
                        <p>{data_inicio}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
            with cols1[1]:
                st.markdown(
                    f"""
                    <div class="card">
                        <h4>📅 Término BL</h4>
                        <p>{data_termino}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
            with cols1[2]:
                st.markdown(
                    f"""
                    <div class="card">
                        <h4>⏳ Duração</h4>
                        <p>{duracao_total} dias</p>
                    </div>
                    """, unsafe_allow_html=True
                )
            with cols1[3]:
                st.markdown(
                    f"""
                    <div class="card">
                        <h4>💰 Valor Agregado</h4>
                        <p>{valor_agregadof}</p>
                    </div>
                    """, unsafe_allow_html=True
                )

            # Linha 2: 4 cards indicadores
            cols2 = st.columns(4, gap="large")
            with cols2[0]:
                st.markdown(
                    f"""
                    <div class="card">
                        <h4>↘️ Latências -</h4>
                        <p>{leads_pct:.2f}%</p>
                        <small>Ideal: = 0%</small>
                    </div>
                    """, unsafe_allow_html=True
                )
            with cols2[1]:
                st.markdown(
                    f"""
                    <div class="card">
                        <h4>↗️ Latências +</h4>
                        <p>{lags_pct:.2f}%</p>
                        <small>Ideal: < 5%</small>
                    </div>
                    """, unsafe_allow_html=True
                )
            with cols2[2]:
                st.markdown(
                    f"""
                    <div class="card">
                        <h4>🔗 Rel. Término-Início</h4>
                        <p>{relationship_types_pct:.2f}%</p>
                        <small>Ideal: > 95%</small>
                    </div>
                    """, unsafe_allow_html=True
                )
            with cols2[3]:
                st.markdown(
                    f"""
                    <div class="card">
                        <h4>🚫 Sem Relacionamento</h4>
                        <p>{logic_pct:.2f}%</p>
                        <small>Ideal: < 5%</small>
                    </div>
                    """, unsafe_allow_html=True
                )

            # Seção da Curva S
            with st.container():
                st.subheader("Curva S")
                with st.spinner("Gerando Curva S..."):
                    curva_s = processar_dados(arquivo_excel, feriados_texto, agrupamento_opcao, s30, s50, s70)
                    if curva_s is not None:
                        # Gráfico da Curva S
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=curva_s.index,
                            y=curva_s['% Acum.'].str.rstrip('%').astype(float),
                            mode='lines+markers',
                            name='% Acum.',
                            line=dict(color='#0068C9')
                        ))
                        fig.add_trace(go.Scatter(
                            x=curva_s.index,
                            y=curva_s['%C30'].str.rstrip('%').astype(float),
                            mode='lines+markers',
                            name='%C30',
                            line=dict(color='#FF9900')
                        ))
                        fig.add_trace(go.Scatter(
                            x=curva_s.index,
                            y=curva_s['%C50'].str.rstrip('%').astype(float),
                            mode='lines+markers',
                            name='%C50',
                            line=dict(color='#FF2D55')
                        ))
                        fig.add_trace(go.Scatter(
                            x=curva_s.index,
                            y=curva_s['%C70'].str.rstrip('%').astype(float),
                            mode='lines+markers',
                            name='%C70',
                            line=dict(color='#00A86B')
                        ))
                        fig.update_layout(
                            title="Curva S - Progresso Acumulado",
                            xaxis_title="Período",
                            yaxis_title="Percentual (%)",
                            template="plotly_white",
                            height=600,
                            font=dict(size=14),
                            margin=dict(l=50, r=50, t=80, b=50)
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        # Tabela da Curva S
                        st.markdown("### Dados da Curva S")
                        st.markdown(
                            """
                            <div class="scrollable-table">
                                <style>
                                .scrollable-table table {
                                    width: 100%;
                                    border-collapse: collapse;
                                }
                                </style>
                            """, unsafe_allow_html=True
                        )
                        st.dataframe(curva_s[['Custo Total', '% ', '% Acum.', '%C30', '%C50', '%C70']],
                                     use_container_width=True)
                    else:
                        st.error("Não foi possível gerar a Curva S. Verifique o arquivo Excel e os feriados.")

            # Seção de Tarefas Críticas e Gantt
            with st.container():
                st.subheader("Tarefas Críticas e Gráfico de Gantt")
                with st.spinner("Gerando análise de tarefas críticas..."):
                    tabela_critica, fig_gantt = caminho_critico_com_gantt(df)
                    if not tabela_critica.empty:
                        # Tabela de Tarefas Críticas
                        st.markdown("### Tarefas Críticas")
                        st.markdown(
                            """
                            <div class="scrollable-table">
                                <style>
                                .scrollable-table table {
                                    width: 100%;
                                    border-collapse: collapse;
                                }
                                </style>
                            """, unsafe_allow_html=True
                        )
                        tabela_critica['Início BL'] = pd.to_datetime(tabela_critica['Início BL']).dt.strftime(
                            '%d/%m/%Y')
                        tabela_critica['Término BL'] = pd.to_datetime(tabela_critica['Término BL']).dt.strftime(
                            '%d/%m/%Y')
                        st.dataframe(tabela_critica, use_container_width=True)

                        # Gráfico de Gantt
                        st.markdown("### Gráfico de Gantt")
                        st.plotly_chart(fig_gantt, use_container_width=True)
                    else:
                        st.warning("Nenhuma tarefa crítica encontrada no cronograma.")

            # Seção de Análise de Alta e Baixa Duração
            with st.container():
                st.subheader("Análise de Alta e Baixa Duração")
                with st.spinner("Analisando durações das tarefas..."):
                    tarefas_alta, tarefas_baixa = analisar_duracao(df, limite_alta, limite_baixa)
                    for tabela in [tarefas_alta, tarefas_baixa]:
                        if not tabela.empty:
                            tabela['Início BL'] = pd.to_datetime(tabela['Início BL']).dt.strftime('%d/%m/%Y')
                            tabela['Término BL'] = pd.to_datetime(tabela['Término BL']).dt.strftime('%d/%m/%Y')

                    # Tabela de Tarefas de Alta Duração
                    st.markdown(f"### Tarefas com Alta Duração (>= {limite_alta} dias)")
                    if not tarefas_alta.empty:
                        st.markdown(
                            """
                            <div class="scrollable-table">
                                <style>
                                .scrollable-table table {
                                    width: 100%;
                                    border-collapse: collapse;
                                }
                                </style>
                            """, unsafe_allow_html=True
                        )
                        st.dataframe(tarefas_alta, use_container_width=True)
                    else:
                        st.warning(f"Nenhuma tarefa com duração >= {limite_alta} dias encontrada.")

                    # Tabela de Tarefas de Baixa Duração
                    st.markdown(f"### Tarefas com Baixa Duração (<= {limite_baixa} dias)")
                    if not tarefas_baixa.empty:
                        st.markdown(
                            """
                            <div class="scrollable-table">
                                <style>
                                .scrollable-table table {
                                    width: 100%;
                                    border-collapse: collapse;
                                }
                                </style>
                            """, unsafe_allow_html=True
                        )
                        st.dataframe(tarefas_baixa, use_container_width=True)
                    else:
                        st.warning(f"Nenhuma tarefa com duração <= {limite_baixa} dias encontrada.")

            # Seção de Análise de Folga Curta
            with st.container():
                st.subheader("Análise de Folga Curta")
                with st.spinner("Analisando tarefas com folga curta..."):
                    tarefas_folga_curta = analisar_folga_curta(df, limite_folga)
                    for tabela in [tarefas_folga_curta]:
                        if not tabela.empty:
                            tabela['Início BL'] = pd.to_datetime(tabela['Início BL']).dt.strftime('%d/%m/%Y')
                            tabela['Término BL'] = pd.to_datetime(tabela['Término BL']).dt.strftime('%d/%m/%Y')

                    # Tabela de Tarefas com Folga Curta
                    st.markdown(f"### Tarefas com Folga Curta (<= {limite_folga} dias)")
                    if not tarefas_folga_curta.empty:
                        st.markdown(
                            """
                            <div class="scrollable-table">
                                <style>
                                .scrollable-table table {
                                    width: 100%;
                                    border-collapse: collapse;
                                }
                                </style>
                            """, unsafe_allow_html=True
                        )
                        st.dataframe(tarefas_folga_curta, use_container_width=True)
                    else:
                        st.warning(f"Nenhuma tarefa com folga <= {limite_folga} dias encontrada.")


else:
    st.info("Por favor, carregue um arquivo Excel para começar a análise.")
    st.markdown(
        """
    ### Por favor, verifique se o seu arquivo contém as seguintes colunas:

    - **Início Agendado** 
    - **Término Agendado** 
    - **Início da Linha de Base** 
    - **Término da linha de base** 
    - **Duração da Linha de Base** 
    - **Margem de atraso permitida** 
    - **Predecessoras**
    - **Sucessoras**
    - **Resumo** 
    - **Custo** 
    - **Nome da tarefa** 
    - **Crítica** 
    - **Duração** 
    - **Quant. Prev.** 
    - **Produtividade** 

    ### Informação Adicional:

    A Curva S é elaborada considerando o calendário sem feriados. Para que o cálculo seja realizado corretamente, é necessário informar as datas de feriado do seu cronograma.

    Verifique se todas essas colunas estão presentes e corretamente formatadas em seu arquivo XLSX.
    """, unsafe_allow_html=True
    )