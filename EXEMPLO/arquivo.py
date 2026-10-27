import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Cuidados",
    layout="wide",
    page_icon="🧹"
)


# Função para carregar os dados do Excel
@st.cache_data
def carregar_dados(caminho_arquivo):
    xls = pd.ExcelFile(caminho_arquivo)

    # Filtrar apenas as abas dos anos
    abas_anos = [
        sheet for sheet in xls.sheet_names
        if "(CV)" not in sheet
    ]

    dados_totais = []

    for ano in abas_anos:
        df_raw = pd.read_excel(xls, sheet_name=ano)

        # Localizar o início dos dados
        indices = df_raw.index[
            df_raw.iloc[:, 0].astype(str).str.strip() == "Brasil"
        ]

        if len(indices) == 0:
            continue

        start_idx = indices[0]

        # Selecionar as colunas relevantes
        df_ano = df_raw.iloc[
            start_idx:, [0, 1, 2, 3]
        ].copy()

        df_ano.columns = [
            "Localidade", "Total", "Homem", "Mulher"
        ]

        # Limpar localidades vazias
        df_ano = df_ano.dropna(subset=["Localidade"])
        df_ano = df_ano[
            df_ano["Localidade"].astype(str).str.strip() != ""
        ]

        # Converter colunas numéricas
        for col in ["Total", "Homem", "Mulher"]:
            df_ano[col] = pd.to_numeric(
                df_ano[col], errors="coerce"
            )

        # Registrar o ano
        df_ano["Ano"] = str(ano)
        dados_totais.append(df_ano)

    # Consolidar todos os anos
    if not dados_totais:
        raise ValueError(
            "Nenhum dado válido foi encontrado nas abas do Excel."
        )

    df_completo = pd.concat(
        dados_totais, ignore_index=True
    )

    return df_completo


# Caminho do arquivo Excel
caminho_arquivo = r"EXEMPLO\Tabela 1.1.2.xls"


try:
    # Carregar os dados
    df = carregar_dados(caminho_arquivo)

    # ---------------- BARRA LATERAL ----------------
    st.sidebar.header("🔍 Filtros")

    # Seleção de ano
    anos_disponiveis = sorted(
        df["Ano"].unique(), reverse=True
    )

    ano_selecionado = st.sidebar.selectbox(
        "Selecione o ano:",
        anos_disponiveis
    )

    # Seleção de localidades
    localidades_disponiveis = (
        df["Localidade"].drop_duplicates().tolist()
    )

    localidades_padrao = [
        "Brasil", "Norte", "Nordeste",
        "Sudeste", "Sul", "Centro-Oeste"
    ]

    # Mostrar apenas localidades padrão que existem nos dados
    localidades_padrao = [
        local for local in localidades_padrao
        if local in localidades_disponiveis
    ]

    localidades_selecionadas = st.sidebar.multiselect(
        "Selecione as Regiões/UFs:",
        options=localidades_disponiveis,
        default=localidades_padrao
    )

    # ---------------- CORPO DA APLICAÇÃO ----------------
    st.title(
        "📊 Horas dedicadas a cuidados e afazeres domésticos"
    )

    st.markdown(
        "Análise da média de horas semanais dedicadas por "
        "pessoas ocupadas de 14 anos ou mais, por sexo."
    )

    # Filtrar os dados
    df_filtrado = df[
        (df["Ano"] == ano_selecionado)
        & (df["Localidade"].isin(localidades_selecionadas))
    ]

    if not df_filtrado.empty:

        # ---------------- TABELA ----------------
        st.subheader(
            f"📋 Dados em tabela ({ano_selecionado})"
        )

        st.dataframe(
            df_filtrado[
                ["Localidade", "Total", "Homem", "Mulher"]
            ].reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("📈 Gráficos Comparativos")

        col1, col2 = st.columns(2)

        # ---------------- GRÁFICO DE BARRAS ----------------
        with col1:
            df_melted = df_filtrado.melt(
                id_vars=["Localidade"],
                value_vars=["Homem", "Mulher"],
                var_name="Gênero",
                value_name="Horas semanais"
            )

            fig_bar = px.bar(
                df_melted,
                x="Localidade",
                y="Horas semanais",
                color="Gênero",
                barmode="group",
                title=f"Média de horas por gênero ({ano_selecionado})",
                color_discrete_sequence=[
                    "#1f77b4", "#e377c2"
                ],
                labels={
                    "Horas semanais": "Horas/Semana",
                    "Localidade": "Região/UF",
                    "Gênero": "Sexo"
                }
            )

            fig_bar.update_layout(
                xaxis_title="Região/UF",
                yaxis_title="Horas por semana",
                legend_title="Sexo"
            )

            st.plotly_chart(
                fig_bar,
                use_container_width=True
            )

        # ---------------- GRÁFICO DE LINHAS ----------------
        with col2:
            df_historico = df[
                df["Localidade"].isin(
                    localidades_selecionadas
                )
            ].copy()

            # Ordenar os anos para a evolução temporal
            df_historico = df_historico.sort_values(
                by="Ano"
            )

            fig_line = px.line(
                df_historico,
                x="Ano",
                y="Total",
                color="Localidade",
                markers=True,
                title="Evolução temporal do total de horas dedicadas",
                labels={
                    "Total": "Horas/Semana",
                    "Ano": "Ano",
                    "Localidade": "Região/UF"
                }
            )

            fig_line.update_layout(
                xaxis_title="Ano",
                yaxis_title="Horas por semana",
                legend_title="Região/UF"
            )

            st.plotly_chart(
                fig_line,
                use_container_width=True
            )

    else:
        st.warning(
            "Nenhuma localidade selecionada nos filtros "
            "da barra lateral."
        )


except Exception as e:
    st.error(f"Erro ao carregar ou processar os dados: {e}")

    st.info(
        "Verifique se o arquivo 'Tabela 1.1.2.xls' existe "
        "no caminho informado e se as bibliotecas necessárias "
        "estão instaladas."
    )
    
