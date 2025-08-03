import pandas as pd
import streamlit as st
import re

def analisar_cadeias_folga_curta(df, limite_folga):
    """
    Analisa tarefas com folga curta e suas cadeias até o caminho crítico, retornando uma tabela com
    a tarefa, sua folga, a cadeia de sucessoras até uma tarefa crítica e a folga total da cadeia.

    Args:
        df (pd.DataFrame): DataFrame com dados do cronograma.
        limite_folga (float): Limite em dias para considerar folga curta.

    Returns:
        pd.DataFrame: Tabela com colunas ['Tarefa', 'Folga (dias)', 'Cadeia até Caminho Crítico', 'Folga Total da Cadeia (dias)'].
    """
    try:
        # Verificar colunas necessárias
        colunas_desejadas = ['Nome da tarefa', 'Folga', 'Sucessoras', 'Crítica']
        if not all(col in df.columns for col in colunas_desejadas):
            st.error("Colunas necessárias para análise de cadeias de folga curta não encontradas.")
            return pd.DataFrame(
                columns=['Tarefa', 'Folga (dias)', 'Cadeia até Caminho Crítico', 'Folga Total da Cadeia (dias)'])

        # Copiar DataFrame
        df = df.copy()

        # Garantir que a coluna Folga é numérica, removendo ' dias' se presente
        df['Folga'] = df['Folga'].astype(str).str.replace(' dias', '', regex=False)
        df['Folga'] = pd.to_numeric(df['Folga'], errors='coerce').fillna(0)

        # Filtrar tarefas com folga curta (0 < Folga <= limite_folga)
        tarefas_folga_curta = df[(df['Folga'] > 0) & (df['Folga'] <= limite_folga)][
            ['Nome da tarefa', 'Folga', 'Sucessoras', 'Crítica']]

        if tarefas_folga_curta.empty:
            st.warning(f"Nenhuma tarefa com folga curta (<= {limite_folga} dias) encontrada.")
            return pd.DataFrame(
                columns=['Tarefa', 'Folga (dias)', 'Cadeia até Caminho Crítico', 'Folga Total da Cadeia (dias)'])

        # Função para extrair IDs de tarefas das sucessoras
        def extrair_ids_sucessoras(sucessoras):
            if pd.isna(sucessoras) or sucessoras == '':
                return []
            # Remover notações como 'TI+33 dias', 'TT', etc., mantendo apenas IDs
            ids = re.split(';|,', str(sucessoras))
            return [re.sub(r'[^0-9]', '', id) for id in ids if re.sub(r'[^0-9]', '', id).isdigit()]

        # Função para rastrear a cadeia até uma tarefa crítica
        def rastrear_cadeia(tarefa_idx, df):
            cadeia = []
            folga_total = 0
            current_idx = tarefa_idx
            visited = set()  # Evitar loops

            while current_idx and current_idx not in visited:
                tarefa = df[df.index == int(current_idx)]
                if tarefa.empty:
                    break
                tarefa_row = tarefa.iloc[0]
                cadeia.append(tarefa_row['Nome da tarefa'])
                folga_total += tarefa_row['Folga']

                if tarefa_row['Crítica'] == 'Sim':
                    break

                visited.add(current_idx)
                sucessoras = extrair_ids_sucessoras(tarefa_row['Sucessoras'])

                # Escolher a sucessora com menor folga (mais próxima do caminho crítico)
                min_folga = float('inf')
                proxima_tarefa = None
                for suc_idx in sucessoras:
                    suc = df[df.index == int(suc_idx)]
                    if not suc.empty and suc['Folga'].iloc[0] < min_folga:
                        min_folga = suc['Folga'].iloc[0]
                        proxima_tarefa = suc_idx

                current_idx = proxima_tarefa

            return cadeia, folga_total

        # Criar tabela de resultados
        resultados = []
        for idx, row in tarefas_folga_curta.iterrows():
            cadeia, folga_total = rastrear_cadeia(idx, df)
            resultados.append({
                'Tarefa': row['Nome da tarefa'],
                'Folga (dias)': row['Folga'],
                'Cadeia até Caminho Crítico': ' → '.join(cadeia),
                'Folga Total da Cadeia (dias)': folga_total
            })

        tabela_resultados = pd.DataFrame(resultados)
        tabela_resultados = tabela_resultados.sort_values(by='Folga Total da Cadeia (dias)')

        return tabela_resultados
    except Exception as e:
        st.error(f"Erro ao analisar cadeias de folga curta: {str(e)}")
        return pd.DataFrame(
            columns=['Tarefa', 'Folga (dias)', 'Cadeia até Caminho Crítico', 'Folga Total da Cadeia (dias)'])

def simular_atraso_caminho_critico(df, tarefa_idx, dias_atraso):
    """
    Simula o impacto de um atraso em uma tarefa com folga curta, recalculando as datas e o caminho crítico,
    considerando diferentes tipos de relacionamentos (FS, SS, FF, SF) e lags/leads.

    Args:
        df (pd.DataFrame): DataFrame com dados do cronograma.
        tarefa_idx (int): Índice da tarefa a ser atrasada.
        dias_atraso (float): Número de dias de atraso.

    Returns:
        tuple: (tabela_impacto, tabela_novo_critico, nova_data_termino)
            - tabela_impacto: Tabela com tarefas impactadas, novas datas e folgas.
            - tabela_novo_critico: Novo caminho crítico (tarefas com folga = 0 após atraso).
            - nova_data_termino: Nova data de término do projeto (ou None se não calculada).
    """
    try:
        # Verificar colunas necessárias
        colunas_desejadas = ['Nome da tarefa', 'Início BL', 'Término BL', 'Duração BL', 'Folga', 'Sucessoras', 'Crítica']
        if not all(col in df.columns for col in colunas_desejadas):
            st.error("Colunas necessárias para simulação de atraso não encontradas.")
            return pd.DataFrame(), pd.DataFrame(), None

        # Copiar DataFrame
        df_sim = df.copy()

        # Garantir formatos
        df_sim['Início BL'] = pd.to_datetime(df_sim['Início BL'], errors='coerce')
        df_sim['Término BL'] = pd.to_datetime(df_sim['Término BL'], errors='coerce')
        df_sim['Folga'] = df_sim['Folga'].astype(str).str.replace(' dias', '', regex=False)
        df_sim['Folga'] = pd.to_numeric(df_sim['Folga'], errors='coerce').fillna(0)
        df_sim['Duração BL'] = pd.to_numeric(df_sim['Duração BL'], errors='coerce').fillna(0)

        # Verificar se tarefa_idx existe
        if tarefa_idx not in df_sim.index:
            st.error(f"Tarefa com índice {tarefa_idx} não encontrada.")
            return pd.DataFrame(), pd.DataFrame(), None

        # Função para extrair IDs, tipo de relacionamento e lag/lead das sucessoras
        def extrair_ids_sucessoras(sucessoras):
            if pd.isna(sucessoras) or sucessoras == '':
                return []
            # Separar sucessoras por ; ou ,
            ids = re.split(';|,', str(sucessoras))
            sucessoras_lista = []
            for item in ids:
                # Extrair ID, tipo de relacionamento e lag/lead
                match = re.match(r'(\d+)(FS|SS|FF|SF)?(?:([+-]\d+)(?:\s*dias)?)?', item.strip())
                if match:
                    task_id = match.group(1)
                    rel_type = match.group(2) or 'FS'  # Default para FS se não especificado
                    lag = int(match.group(3) or 0)  # Default para 0 se não especificado
                    sucessoras_lista.append({'id': task_id, 'rel_type': rel_type, 'lag': lag})
            return sucessoras_lista

        # Inicializar listas para rastrear impacto
        tarefas_impactadas = []
        visited = set()

        # Função para propagar atraso
        def propagar_atraso(current_idx, atraso_inicio, atraso_termino):
            if current_idx in visited or current_idx not in df_sim.index:
                return
            visited.add(current_idx)
            tarefa = df_sim[df_sim.index == int(current_idx)].iloc[0]
            folga_original = tarefa['Folga']
            # O atraso absorvido é limitado pela folga total
            atraso_absorvido = min(folga_original, max(atraso_inicio, atraso_termino))
            atraso_propagado = max(atraso_inicio, atraso_termino) - atraso_absorvido
            nova_folga = folga_original - atraso_absorvido

            # Ajustar datas com base no atraso
            novo_inicio = tarefa['Início BL'] + pd.Timedelta(days=atraso_inicio)
            novo_termino = tarefa['Término BL'] + pd.Timedelta(days=atraso_termino)

            # Garantir que a duração seja mantida
            duracao_esperada = tarefa['Duração BL']
            duracao_atual = (novo_termino - novo_inicio).days
            if duracao_atual != duracao_esperada:
                novo_termino = novo_inicio + pd.Timedelta(days=duracao_esperada)

            # Registrar tarefa impactada
            tarefas_impactadas.append({
                'Tarefa': tarefa['Nome da tarefa'],
                'Índice': current_idx,
                'Início Original': tarefa['Início BL'].strftime('%d/%m/%y'),
                'Término Original': tarefa['Término BL'].strftime('%d/%m/%y'),
                'Início Novo': novo_inicio.strftime('%d/%m/%y'),
                'Término Novo': novo_termino.strftime('%d/%m/%y'),
                'Folga Original (dias)': folga_original,
                'Nova Folga (dias)': nova_folga,
                'Atraso Aplicado (Início, dias)': atraso_inicio,
                'Atraso Aplicado (Término, dias)': atraso_termino
            })

            # Atualizar DataFrame simulado
            df_sim.loc[df_sim.index == current_idx, 'Início BL'] = novo_inicio
            df_sim.loc[df_sim.index == current_idx, 'Término BL'] = novo_termino
            df_sim.loc[df_sim.index == current_idx, 'Folga'] = nova_folga
            df_sim.loc[df_sim.index == current_idx, 'Crítica'] = 'Sim' if nova_folga == 0 else 'Não'

            # Propagar atraso para sucessoras com base no tipo de relacionamento
            sucessoras = extrair_ids_sucessoras(tarefa['Sucessoras'])
            for suc in sucessoras:
                suc_idx = int(suc['id'])
                rel_type = suc['rel_type']
                lag = suc['lag']

                # Calcular atraso propagado com base no tipo de relacionamento
                if rel_type == 'FS':
                    novo_atraso_inicio = atraso_propagado + lag
                    novo_atraso_termino = atraso_propagado + lag
                elif rel_type == 'SS':
                    novo_atraso_inicio = atraso_inicio + lag
                    novo_atraso_termino = atraso_inicio + lag  # SS afeta o início, término ajustado pela duração
                elif rel_type == 'FF':
                    novo_atraso_inicio = atraso_termino + lag - df_sim.loc[suc_idx, 'Duração BL']
                    novo_atraso_termino = atraso_termino + lag
                elif rel_type == 'SF':
                    novo_atraso_inicio = atraso_termino + lag
                    novo_atraso_termino = atraso_termino + lag + df_sim.loc[suc_idx, 'Duração BL']
                else:
                    continue  # Ignorar tipos desconhecidos

                propagar_atraso(suc_idx, max(0, novo_atraso_inicio), max(0, novo_atraso_termino))

        # Iniciar propagação do atraso na tarefa inicial
        tarefa_inicial = df_sim[df_sim.index == int(tarefa_idx)].iloc[0]
        propagar_atraso(tarefa_idx, dias_atraso, dias_atraso)

        # Criar tabela de impacto
        tabela_impacto = pd.DataFrame(tarefas_impactadas)
        if tabela_impacto.empty:
            st.warning("Nenhuma tarefa impactada pelo atraso.")
            tabela_impacto = pd.DataFrame(columns=[
                'Tarefa', 'Índice', 'Início Original', 'Término Original',
                'Início Novo', 'Término Novo', 'Folga Original (dias)', 'Nova Folga (dias)',
                'Atraso Aplicado (Início, dias)', 'Atraso Aplicado (Término, dias)'
            ])

        # Identificar novo caminho crítico (tarefas com folga = 0)
        tabela_novo_critico = df_sim[df_sim['Folga'] == 0][
            ['Nome da tarefa', 'Início BL', 'Término BL', 'Duração BL', 'Folga']
        ].copy()
        tabela_novo_critico['Início BL'] = tabela_novo_critico['Início BL'].dt.strftime('%d/%m/%y')
        tabela_novo_critico['Término BL'] = tabela_novo_critico['Término BL'].dt.strftime('%d/%m/%y')
        if tabela_novo_critico.empty:
            st.warning("Nenhum novo caminho crítico identificado após o atraso.")

        # Calcular nova data de término do projeto
        nova_data_termino = df_sim['Término BL'].max()
        if pd.isna(nova_data_termino):
            nova_data_termino = None
        else:
            nova_data_termino = nova_data_termino.strftime('%d/%m/%y')

        return tabela_impacto, tabela_novo_critico, nova_data_termino

    except Exception as e:
        st.error(f"Erro ao simular atraso: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), None