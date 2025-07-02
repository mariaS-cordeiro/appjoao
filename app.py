import altair as alt
import pandas as pd
import streamlit as st

# Função para carregar dados a partir do arquivo enviado
@st.cache_data
def load_data(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)

        # Renomeia coluna se necessário
        df.rename(columns={'seguidores_x': 'seguidores_twitter'}, inplace=True)

        # Garante colunas necessárias com valores válidos
        for col in ['seguidores_twitter', 'curtidas_instagram', 'visualizacoes_tiktok']:
            if col not in df.columns:
                df[col] = 0
            df[col] = df[col].fillna(0).astype(int)

        return df

    except Exception as e:
        st.error(f"Erro ao carregar o arquivo CSV: {e}")
        return pd.DataFrame()

# Função para criar gráficos com Altair
def create_bar_chart(data, x_col, y_col, title):
    x_axis_title = title.split("por ")[1] if "por " in title else x_col
    return alt.Chart(data).mark_bar().encode(
        x=alt.X(x_col, title=x_axis_title),
        y=alt.Y(y_col, sort='-x', title='Nome do Deputado'),
        tooltip=[y_col, x_col, 'partido', 'uf']
    ).properties(
        title=title
    ).interactive()

# Função principal
def main():
    st.set_page_config(page_title="Análise de Deputados – Upload de CSV", layout="wide")
    st.title("📊 Análise de Engajamento de Deputados nas Redes Sociais")

    st.markdown("""
    **🔽 Para começar, envie um arquivo .CSV com os dados dos deputados.**
    
    O arquivo deve conter, pelo menos, as colunas:
    `nome_deputado`, `partido`, `uf`, `seguidores_twitter`, `curtidas_instagram`, `visualizacoes_tiktok`
    """)

    uploaded_file = st.file_uploader("📁 Envie o arquivo CSV", type=["csv"], help="Envie sua base de dados de deputados")

    if uploaded_file is None:
        st.warning("Por favor, envie um arquivo CSV para visualizar os dados.")
        return

    with st.spinner("Carregando dados..."):
        df = load_data(uploaded_file)

    if df.empty:
        st.warning("Nenhum dado encontrado no arquivo CSV enviado.")
        return

    # --- Filtros na barra lateral ---
    st.sidebar.header("🎯 Filtros")
    ufs = ["Todas"] + sorted(df['uf'].dropna().unique().tolist())
    partidos = ["Todos"] + sorted(df['partido'].dropna().unique().tolist())

    selected_uf = st.sidebar.selectbox("Filtrar por UF:", ufs)
    selected_partido = st.sidebar.selectbox("Filtrar por Partido:", partidos)
    search_name = st.sidebar.text_input("Pesquisar por Nome do Deputado:")

    filtered_df = df.copy()
    if selected_uf != "Todas":
        filtered_df = filtered_df[filtered_df['uf'] == selected_uf]
    if selected_partido != "Todos":
        filtered_df = filtered_df[filtered_df['partido'] == selected_partido]
    if search_name:
        filtered_df = filtered_df[filtered_df['nome_deputado'].str.contains(search_name, case=False, na=False)]

    # --- Tabela de Deputados ---
    st.subheader(f"📋 Lista de Deputados Filtrados ({len(filtered_df)} encontrados)")
    if not filtered_df.empty:
        cols_to_display = ['nome_deputado', 'partido', 'uf', 'seguidores_twitter', 'curtidas_instagram', 'visualizacoes_tiktok']
        st.dataframe(
            filtered_df[cols_to_display].style
            .format({
                'seguidores_twitter': '{:,.0f}',
                'curtidas_instagram': '{:,.0f}',
                'visualizacoes_tiktok': '{:,.0f}'
            })
            .highlight_max(subset=['seguidores_twitter', 'curtidas_instagram', 'visualizacoes_tiktok'], color='#d3f9d8')
        )

        # Botão para download dos dados filtrados
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar dados filtrados", data=csv, file_name="dados_deputados_filtrados.csv", mime="text/csv")
    else:
        st.info("Nenhum deputado encontrado com os filtros selecionados.")

    # --- Gráficos de Top N ---
    st.subheader("📊 Visualizações de Engajamento por Plataforma")
    num_top = st.slider("Número de deputados a exibir:", 5, 20, 10)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"### Top {num_top} por Seguidores no X (Twitter)")
        top_twitter = filtered_df.nlargest(num_top, 'seguidores_twitter')
        st.altair_chart(create_bar_chart(top_twitter, 'seguidores_twitter', 'nome_deputado', f"Top {num_top} por Seguidores no X"), use_container_width=True)

    with col2:
        st.write(f"### Top {num_top} por Curtidas no Instagram")
        top_instagram = filtered_df.nlargest(num_top, 'curtidas_instagram')
        st.altair_chart(create_bar_chart(top_instagram, 'curtidas_instagram', 'nome_deputado', f"Top {num_top} por Curtidas no Instagram"), use_container_width=True)

    with col3:
        st.write(f"### Top {num_top} por Visualizações no TikTok")
        top_tiktok = filtered_df.nlargest(num_top, 'visualizacoes_tiktok')
        st.altair_chart(create_bar_chart(top_tiktok, 'visualizacoes_tiktok', 'nome_deputado', f"Top {num_top} por Visualizações no TikTok"), use_container_width=True)

# Executa o app
if __name__ == '__main__':
    main()
