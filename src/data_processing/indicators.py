import pandas as pd
import streamlit as st
import numpy as np


def calcular_indicadores(df):
    """
    Calcula indicadores de desempenho do cronograma.

    Args:
        df (pd.DataFrame): DataFrame com dados do cronograma.

    Returns:
        tuple: Percentuais de latências, relacionamentos, datas e duração.
    """
    try:
        quant_tarefas = len(df)
        leads = df['Predecessoras'].apply(lambda x: '+' in x if isinstance(x, str) else False).sum()
        lags = df['Predecessoras'].apply(lambda x: '-' in x if isinstance(x, str) else False).sum()
        relationship_types = df['Predecessoras'].apply(
            lambda x: all(s not in x for s in ['II', 'IT', 'TT']) if isinstance(x, str) else True).sum()
        linhas_vazias = df[(df['Predecessoras'] == '') & (df['Sucessoras'] == '')]
        logic = len(linhas_vazias)
        leads_pct = (leads / quant_tarefas) * 100
        lags_pct = (lags / quant_tarefas) * 100
        relationship_types_pct = (relationship_types / quant_tarefas) * 100
        logic_pct = (logic / quant_tarefas) * 100

        # Garantir que as colunas de data são datetime
        data_inicio = pd.to_datetime(df['Início BL'].min())
        data_termino = pd.to_datetime(df['Término BL'].max())

        # Formatando as datas
        data_inicio_str = data_inicio.strftime("%d/%m/%y") if pd.notna(data_inicio) else "N/A"
        data_termino_str = data_termino.strftime("%d/%m/%y") if pd.notna(data_termino) else "N/A"
        duracao_total = (data_termino - data_inicio).days if pd.notna(data_inicio) and pd.notna(data_termino) else 0

        return leads_pct, lags_pct, relationship_types_pct, logic_pct, data_inicio_str, data_termino_str, duracao_total
    except Exception as e:
        st.error(f"Erro ao calcular indicadores: {str(e)}")
        return 0, 0, 0, 0, "N/A", "N/A", 0


def analisar_duracao(df, limite_alta, limite_baixa):
    """
    Identifica tarefas com alta e baixa duração com base em limites de dias fornecidos pelo usuário.

    Args:
        df (pd.DataFrame): DataFrame com dados do cronograma.
        limite_alta (float): Limite em dias para tarefas de alta duração.
        limite_baixa (float): Limite em dias para tarefas de baixa duração.

    Returns:
        tuple: (tabela_alta, tabela_baixa) com DataFrames das tarefas de alta e baixa duração.
    """
    try:
        # Selecionar colunas relevantes
        colunas_desejadas = ['Nome da tarefa', 'Início BL', 'Término BL', 'Duração BL', 'Quant. Prev.', 'Produtividade']
        if not all(col in df.columns for col in colunas_desejadas):
            st.error("Colunas necessárias para análise de duração não encontradas.")
            return pd.DataFrame(columns=colunas_desejadas), pd.DataFrame(columns=colunas_desejadas)

        # Copiar DataFrame e garantir formato de data
        df = df.copy()
        df['Início BL'] = pd.to_datetime(df['Início BL'])
        df['Término BL'] = pd.to_datetime(df['Término BL'])
        df['Início BL Str'] = df['Início BL'].dt.strftime('%d/%m/%y')
        df['Término BL Str'] = df['Término BL'].dt.strftime('%d/%m/%y')

        # Filtrar tarefas
        tarefas_alta = df[df['Duração BL'] >= limite_alta][colunas_desejadas]
        tarefas_baixa = df[df['Duração BL'] <= limite_baixa][colunas_desejadas]

        # Ordenar por Duração BL
        tarefas_alta = tarefas_alta.sort_values(by='Duração BL', ascending=False)
        tarefas_baixa = tarefas_baixa.sort_values(by='Duração BL')

        return tarefas_alta, tarefas_baixa
    except Exception as e:
        st.error(f"Erro ao analisar durações: {str(e)}")
        return pd.DataFrame(columns=colunas_desejadas), pd.DataFrame(columns=colunas_desejadas)


def analisar_folga_curta(df, limite_folga):
    """
    Identifica tarefas com folga curta com base em um limite de dias fornecido pelo usuário,
    excluindo tarefas com folga igual a 0 (caminho crítico).

    Args:
        df (pd.DataFrame): DataFrame com dados do cronograma.
        limite_folga (float): Limite em dias para considerar folga curta.

    Returns:
        pd.DataFrame: DataFrame com tarefas cuja folga é menor ou igual ao limite e maior que 0.
    """
    try:
        # Selecionar colunas relevantes
        colunas_desejadas = ['Nome da tarefa', 'Início BL', 'Término BL', 'Duração BL', 'Folga']
        if not all(col in df.columns for col in colunas_desejadas):
            st.error("Colunas necessárias para análise de folga não encontradas.")
            return pd.DataFrame(columns=colunas_desejadas)

        # Copiar DataFrame e garantir formato de data
        df = df.copy()
        df['Início BL'] = pd.to_datetime(df['Início BL'])
        df['Término BL'] = pd.to_datetime(df['Término BL'])
        df['Início BL Str'] = df['Início BL'].dt.strftime('%d/%m/%y')
        df['Término BL Str'] = df['Término BL'].dt.strftime('%d/%m/%y')

        # Garantir que a coluna Folga é numérica, removendo ' dias'
        df['Folga'] = df['Folga'].astype(str).str.replace(' dias', '', regex=False)
        df['Folga'] = pd.to_numeric(df['Folga'], errors='coerce').fillna(0)

        # Filtrar tarefas com folga curta (0 < Folga <= limite_folga)
        tarefas_folga_curta = df[(df['Folga'] > 0) & (df['Folga'] <= limite_folga)][colunas_desejadas]

        # Ordenar por Folga
        tarefas_folga_curta = tarefas_folga_curta.sort_values(by='Folga')

        if tarefas_folga_curta.empty:
            st.warning(f"Nenhuma tarefa com folga <= {limite_folga} dias encontrada.")

        return tarefas_folga_curta
    except Exception as e:
        st.error(f"Erro ao analisar folga curta: {str(e)}")
        return pd.DataFrame(columns=colunas_desejadas)