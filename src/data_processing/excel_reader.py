import streamlit as st
import pandas as pd


@st.cache_data
def ler_arquivo_excel(arquivo_excel):
    """
    Lê e processa um arquivo Excel com dados de cronograma.

    Args:
        arquivo_excel: Arquivo Excel carregado via Streamlit file_uploader.

    Returns:
        pandas.DataFrame: DataFrame processado ou None em caso de erro.
    """
    try:
        # Ler o arquivo Excel
        df = pd.read_excel(
            arquivo_excel,
            sheet_name="Planilha1"
        )

        # Renomear colunas esperadas
        rename_map = {
            "Início da Linha de Base": "Início BL",
            "Término da linha de base": "Término BL",
            "Duração da Linha de Base": "Duração BL",
            "Margem de atraso permitida": "Folga"
        }
        df.rename(columns=rename_map, inplace=True)

        # Verificar colunas obrigatórias
        required_columns = ["Início BL", "Término BL", "Duração BL", "Custo", "Nome da tarefa"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Colunas obrigatórias ausentes no arquivo Excel: {', '.join(missing_columns)}")
            return None

        # Verificar se colunas opcionais existem, caso contrário, inicializá-las
        optional_columns = {
            "Predecessoras": "",
            "Sucessoras": "",
            "Crítica": "Não",
            "Quant. Prev.": 0,
            "Produtividade": 0,
            "Folga": 0
        }
        for col, default in optional_columns.items():
            if col not in df.columns:
                df[col] = default

        # Verificar e processar a coluna Resumo (opcional)
        if 'Resumo' in df.columns:
            df = df.query("Resumo == 'Não'").copy()
        else:
            st.warning("Coluna 'Resumo' não encontrada. Todas as linhas serão processadas.")

        # Converter colunas de data para datetime
        date_columns = ["Início Agendado", "Término Agendado", "Início BL", "Término BL"]
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], format='%d.%m.%y', errors='coerce')
                    if df[col].isna().any():
                        st.warning(
                            f"Algumas datas na coluna '{col}' não puderam ser convertidas. Verifique o formato (DD.MM.YY).")
                except Exception as e:
                    st.error(f"Erro ao converter a coluna '{col}' para data: {str(e)}")
                    return None

        # Verificar se as colunas de data obrigatórias contêm valores válidos
        for col in ["Início BL", "Término BL"]:
            if df[col].isna().any():
                st.error(f"A coluna '{col}' contém valores inválidos ou não convertíveis para data.")
                return None

        # Limpar strings em colunas de texto
        df = df.apply(lambda col: col.str.replace('diasd|dias|dia', '',
                                                  regex=True) if col.dtype == 'object' and col.name != 'Produtividade' else col)

        # Garantir que Predecessoras e Sucessoras sejam strings
        df[['Predecessoras', 'Sucessoras']] = df[['Predecessoras', 'Sucessoras']].astype(str)

        # Processar Duração BL
        df['Duração BL'] = df['Duração BL'].astype(str).str.replace(',', '.').str.strip()
        try:
            df['Duração BL'] = df['Duração BL'].astype(float).astype(int)
        except ValueError as e:
            st.error(f"Erro ao converter 'Duração BL' para número inteiro: {str(e)}")
            return None

        # Calcular Custo Diário
        df['Custo Diário'] = df['Custo'] / df['Duração BL']

        return df
    except Exception as e:
        st.error(f"Erro ao processar o arquivo Excel: {str(e)}")
        return None