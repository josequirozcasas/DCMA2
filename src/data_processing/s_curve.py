import streamlit as st
import pandas as pd
import numpy as np
import math


def selecionar_feriados(feriados_texto):
    """
    Converte texto de feriados em uma lista de datas.

    Args:
        feriados_texto (str): Texto com datas no formato DD/MM/YYYY, uma por linha.

    Returns:
        list: Lista de datas (pd.Timestamp) ou lista vazia em caso de erro.
    """
    feriados = []
    for data_texto in feriados_texto.split('\n'):
        data_texto = data_texto.strip()
        if data_texto:
            try:
                feriados.append(pd.to_datetime(data_texto, format='%d/%m/%Y'))
            except ValueError:
                st.error(f"A data '{data_texto}' está em um formato inválido. Use DD/MM/YYYY.")
    return feriados


def criar_curva_s(dataframe, agrupamento, S30, S50, S70):
    """
    Gera a Curva S com base nos dados agrupados.

    Args:
        dataframe (pd.DataFrame): Dados com colunas de custo e data.
        agrupamento (str): Tipo de agrupamento ('Mês' ou 'Semana').
        S30, S50, S70 (float): Fatores para as curvas S30, S50 e S70.

    Returns:
        pd.DataFrame: Curva S com colunas '% ', '% Acum.', 'Custo Total', etc.
    """
    if agrupamento == 'Mês':
        curva_s_agrupado = dataframe.groupby(pd.Grouper(freq='ME')).sum()  # Changed 'M' to 'ME'
        curva_s_agrupado.index = curva_s_agrupado.index.strftime('%m/%y')
        N = len(curva_s_agrupado)
    elif agrupamento == 'Semana':
        curva_s_agrupado = dataframe.groupby(pd.Grouper(freq='W-MON')).sum()
        curva_s_agrupado.index = curva_s_agrupado.index.strftime('%d/%m/%y')
        N = len(curva_s_agrupado)
    else:
        return None

    curva_s_agrupado['n'] = range(0, N)
    curva_s_agrupado['Curva30'] = curva_s_agrupado['n'].apply(
        lambda n: (1 - ((1 - ((n / (N - 1)) ** (math.log10(30)))) ** S30)) * 100)
    curva_s_agrupado['Curva50'] = curva_s_agrupado['n'].apply(
        lambda n: (1 - ((1 - ((n / (N - 1)) ** (math.log10(50)))) ** S50)) * 100)
    curva_s_agrupado['Curva70'] = curva_s_agrupado['n'].apply(
        lambda n: (1 - ((1 - ((n / (N - 1)) ** (math.log10(70)))) ** S70)) * 100)
    curva_s_agrupado['% Acum.'] = curva_s_agrupado['%'].cumsum()
    curva_s_agrupado['Custo Total'] = curva_s_agrupado['Custo Total'].apply(
        lambda x: '{:,.2f}'.format(x).replace(',', 'X').replace('.', ',').replace('X', '.'))
    curva_s_agrupado['% '] = curva_s_agrupado['%'].apply(lambda x: f"{x:.1f}%")
    curva_s_agrupado['% Acum.'] = curva_s_agrupado['% Acum.'].apply(lambda x: f"{x:.1f}%")
    curva_s_agrupado['%C30'] = curva_s_agrupado['Curva30'].apply(lambda x: f"{x:.1f}%")
    curva_s_agrupado['%C50'] = curva_s_agrupado['Curva50'].apply(lambda x: f"{x:.1f}%")
    curva_s_agrupado['%C70'] = curva_s_agrupado['Curva70'].apply(lambda x: f"{x:.1f}%")
    return curva_s_agrupado


def processar_dados(arquivo_excel, feriados_texto, agrupamento_opcao, S30, S50, S70):
    """
    Processa os dados do Excel para gerar a Curva S.

    Args:
        arquivo_excel: Arquivo Excel carregado.
        feriados_texto (str): Texto com feriados.
        agrupamento_opcao (str): 'Mês' ou 'Semana'.
        S30, S50, S70 (float): Fatores para curvas.

    Returns:
        pd.DataFrame: Curva S processada ou None em caso de erro.
    """
    from .excel_reader import ler_arquivo_excel
    if arquivo_excel is not None:
        df = ler_arquivo_excel(arquivo_excel)
        if df is None:
            return None
        df['Folga'] = pd.to_numeric(df['Folga'], errors='coerce')
        feriados = selecionar_feriados(feriados_texto)
        datas_uteis = pd.date_range(start=df['Início BL'].min(), end=df['Término BL'].max(), freq='B')
        if agrupamento_opcao == 'Mês':
            datas_uteis = pd.date_range(start=df['Início BL'].min() - pd.DateOffset(months=1),
                                        end=df['Término BL'].max(), freq='B')
        elif agrupamento_opcao == 'Semana':
            datas_uteis = pd.date_range(start=df['Início BL'].min() - pd.DateOffset(weeks=1),
                                        end=df['Término BL'].max(), freq='B')
        DataS = pd.DataFrame(index=datas_uteis)
        for index, row in df.iterrows():
            data_inicio = row['Início BL']
            data_termino = row['Término BL']
            tarefa = row['Nome da tarefa'].strip()
            custo_total = row['Custo']
            custo_diario = row['Custo Diário']
            if tarefa not in DataS.columns:
                DataS[tarefa] = 0.0  # Initialize as float64
            datas_tarefa = pd.date_range(start=data_inicio, end=data_termino, freq='B')
            for data in datas_tarefa:
                if data not in feriados:
                    DataS.loc[data, tarefa] += custo_diario
        CurvaS = DataS.sum(axis=1).reset_index()
        CurvaS.columns = ['Data', 'Custo Total']
        CurvaS['Data'] = pd.to_datetime(CurvaS['Data'], format='%d.%m.%y')
        CurvaS.set_index('Data', inplace=True)
        CurvaS['Custo Total'] = CurvaS['Custo Total'].replace([np.inf, -np.inf], 0).astype('float64')  # Ensure float64
        custo_total = CurvaS['Custo Total'].sum()
        CurvaS['%'] = round((CurvaS['Custo Total'] / custo_total) * 100, 2).astype('float64')  # Ensure float64
        CurvaS_agrupado = criar_curva_s(CurvaS, agrupamento_opcao, S30, S50, S70).round(1)
        return CurvaS_agrupado
    return None