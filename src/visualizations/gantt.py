import pandas as pd
import plotly.figure_factory as ff
import streamlit as st
from src.data_processing.indicators import analisar_folga_curta


def caminho_critico_com_gantt(df):
    """
    Gera uma tabela e um gráfico de Gantt para as tarefas críticas, ordenadas por data de início,
    com tarefas mais antigas na parte superior do gráfico.

    Args:
        df (pd.DataFrame): DataFrame com dados do cronograma.

    Returns:
        tuple: (tabela_critica, fig_gantt) com a tabela de tarefas críticas e o gráfico de Gantt.
    """
    try:
        colunas_desejadas = ['Nome da tarefa', 'Início BL', 'Término BL', 'Duração BL', 'Quant. Prev.', 'Produtividade']
        if not all(col in df.columns for col in colunas_desejadas):
            st.error("Colunas necessárias para o caminho crítico não encontradas.")
            return pd.DataFrame(columns=colunas_desejadas), None

        df = df.copy()
        df['Início BL'] = pd.to_datetime(df['Início BL'])
        df['Término BL'] = pd.to_datetime(df['Término BL'])
        df['Início BL Str'] = df['Início BL'].dt.strftime('%d/%m/%y')
        df['Término BL Str'] = df['Término BL'].dt.strftime('%d/%m/%y')

        # Filtrar tarefas críticas e ordenar por Início BL
        tabela_critica = df[df['Crítica'] == 'Sim'][colunas_desejadas].sort_values(by='Início BL')

        df_gantt = df[df['Crítica'] == 'Sim'].copy()
        df_gantt = df_gantt.sort_values(by='Início BL')  # Ordenar por data de início

        gantt_data = [
            dict(Task=row['Nome da tarefa'], Start=row['Início BL'], Finish=row['Término BL'], Resource='Crítica')
            for _, row in df_gantt.iterrows()
        ]

        if not gantt_data:
            return tabela_critica, None

        colors = {'Crítica': '#FF2D55'}
        fig_gantt = ff.create_gantt(
            gantt_data,
            colors=colors,
            index_col='Resource',
            title='Gráfico de Gantt - Tarefas Críticas',
            show_colorbar=True,
            bar_width=0.4,
            showgrid_x=True,
            showgrid_y=True
        )
        fig_gantt.update_layout(
            xaxis_title="Período",
            yaxis_title="Tarefas",
            template="plotly_white",
            height=400 + len(gantt_data) * 20,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        fig_gantt.update_yaxes(autorange="reversed")  # Inverter o eixo Y

        return tabela_critica, fig_gantt
    except Exception as e:
        st.error(f"Erro ao gerar gráfico de Gantt: {str(e)}")
        return pd.DataFrame(columns=colunas_desejadas), None


def gantt_folga_curta(df, limite_folga):
    """
    Gera um gráfico de Gantt para tarefas críticas e tarefas com folga curta, ordenadas por data de início,
    usando vermelho para críticas e laranja para folga curta, com tarefas mais antigas na parte superior.

    Args:
        df (pd.DataFrame): DataFrame com dados do cronograma.
        limite_folga (float): Limite em dias para considerar folga curta.

    Returns:
        tuple: (tabela_folga_curta, fig_gantt) com a tabela de tarefas com folga curta e o gráfico de Gantt.
    """
    try:
        # Obter tarefas com folga curta
        tabela_folga_curta = analisar_folga_curta(df, limite_folga)

        # Obter tarefas críticas
        colunas_desejadas = ['Nome da tarefa', 'Início BL', 'Término BL', 'Duração BL', 'Folga']
        if not all(col in df.columns for col in colunas_desejadas):
            st.error("Colunas necessárias para análise de folga não encontradas.")
            return tabela_folga_curta, None

        df = df.copy()
        df['Início BL'] = pd.to_datetime(df['Início BL'])
        df['Término BL'] = pd.to_datetime(df['Término BL'])

        # Filtrar tarefas críticas
        df_criticas = df[df['Crítica'] == 'Sim'][colunas_desejadas].copy()

        # Combinar tarefas críticas e com folga curta
        df_combinado = pd.concat([df_criticas, tabela_folga_curta]).drop_duplicates(subset=['Nome da tarefa'])
        df_combinado = df_combinado.sort_values(by='Início BL')  # Ordenar por data de início

        # Preparar dados para o gráfico de Gantt
        gantt_data = []
        for _, row in df_combinado.iterrows():
            resource = 'Crítica' if row['Nome da tarefa'] in df_criticas['Nome da tarefa'].values else 'Folga Curta'
            gantt_data.append(
                dict(Task=row['Nome da tarefa'], Start=row['Início BL'], Finish=row['Término BL'], Resource=resource)
            )

        if not gantt_data:
            return tabela_folga_curta, None

        colors = {'Crítica': '#FF2D55', 'Folga Curta': '#FF9900'}  # Vermelho para críticas, laranja para folga curta
        fig_gantt = ff.create_gantt(
            gantt_data,
            colors=colors,
            index_col='Resource',
            title='Gráfico de Gantt - Tarefas Críticas e com Folga Curta',
            show_colorbar=True,
            bar_width=0.4,
            showgrid_x=True,
            showgrid_y=True
        )
        fig_gantt.update_layout(
            xaxis_title="Período",
            yaxis_title="Tarefas",
            template="plotly_white",
            height=400 + len(gantt_data) * 20,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        fig_gantt.update_yaxes(autorange="reversed")  # Inverter o eixo Y

        return tabela_folga_curta, fig_gantt
    except Exception as e:
        st.error(f"Erro ao gerar gráfico de Gantt para folga curta: {str(e)}")
        return pd.DataFrame(columns=['Nome da tarefa', 'Início BL', 'Término BL', 'Duração BL', 'Folga']), None