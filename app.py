import altair as alt
import pandas as pd
import streamlit as st
from io import StringIO

# Função para carregar dados dos deputados
@st.cache_data
def load_data(uploaded_file=None):
    try:
        if uploaded_file is not None:
            df_deputados = pd.read_csv(uploaded_file)
        else:
            df_deputados = pd.read_csv('engajamentodeputados.csv')

        # Supondo que engajamento seja o mesmo arquivo ou outro - ajuste se necessário
        df_engajamento = df_deputados.copy()

        df_completo = pd.merge(df_deputados, df_engajamento, on='nome_deputado', how='left')

        # Ajustes de colunas esperadas
        df_completo.rename(columns={'seguidores_x': 'seguidores_twitter'}, inplace=True)

        for col in ['seguidores_twitter', 'curtidas_instagram', 'visualizacoes_tiktok']:
            if col not in df_completo.columns:
                df_completo[col] = 0
            df_completo[col] = df_completo[col].fillna(0).astype(int)

        return df_completo

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Função para carregar os posts
@st.cache_data
def load_posts():
    try:
        df_posts = pd.read_csv('engajamentodeputados.csv', delimiter=';')
        df_posts['Date'] = pd.to_datetime(df_posts['Date'], errors='coerce')
        df_posts['Engajamento total'] = pd.to_numeric(df_posts['Engajamento total'], errors='coerce').fillna(0).astype(int)
        return df_posts
    except Exception as e:
        st.error(f"Erro ao carregar Posts.csv: {e}")
        return pd.DataFrame()

# Função para criar gráfico de barras com Altair
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
    st.set_page_config(page_title="Análise de Deputados e Posts", layout="wide")

    st.title("📊 Análise de Deputados e Engajamento + Posts nas Redes Sociais")

    st.sidebar.header("🔽 Upload de Dados")
    uploaded_file = st.sidebar.file_uploader("Envie um arquivo CSV com dados de deputados", type=["csv"])

    # Carregar os dados com base no upload ou arquivo local
    with st.spinner("Carregando dados dos deputados..."):
        df = load_data(uploaded_file)

    if df.empty:
        st.warning("Não foi possível carregar os dados dos deputados.")
        return

    # Filtros
    st.sidebar.header("🎯 Filtros de Deputados")
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

    # Tabela de Deputados
    st.subheader(f"📋 Lista de Deputados ({len(filtered_df)} encontrados)")
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

        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar dados filtrados", data=csv, file_name="dados_deputados_filtrados.csv", mime="text/csv")
    else:
        st.info("Nenhum deputado encontrado com os filtros selecionados.")

    # Gráficos
    st.subheader("📊 Visualizações de Engajamento por Plataforma")
    num_top_deputies = st.slider("Número de deputados para exibir nos gráficos:", 5, 20, 10)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"### Top {num_top_deputies} por Seguidores no X")
        top_x = filtered_df.nlargest(num_top_deputies, 'seguidores_twitter')
        if not top_x.empty:
            st.altair_chart(create_bar_chart(top_x, 'seguidores_twitter', 'nome_deputado', f"Top {num_top_deputies} por Seguidores no X"), use_container_width=True)
    with col2:
        st.write(f"### Top {num_top_deputies} por Curtidas no Instagram")
        top_instagram = filtered_df.nlargest(num_top_deputies, 'curtidas_instagram')
        if not top_instagram.empty:
            st.altair_chart(create_bar_chart(top_instagram, 'curtidas_instagram', 'nome_deputado', f"Top {num_top_deputies} por Curtidas no Instagram"), use_container_width=True)
    with col3:
        st.write(f"### Top {num_top_deputies} por Visualizações no TikTok")
        top_tiktok = filtered_df.nlargest(num_top_deputies, 'visualizacoes_tiktok')
        if not top_tiktok.empty:
            st.altair_chart(create_bar_chart(top_tiktok, 'visualizacoes_tiktok', 'nome_deputado', f"Top {num_top_deputies} por Visualizações no TikTok"), use_container_width=True)

    st.markdown("---")

    # Análise de Posts
    st.header("📱 Top N Posts por Engajamento")
    df_posts = load_posts()

    if df_posts.empty:
        st.warning("Nenhum dado de posts encontrado.")
    else:
        redes = ["Todas"] + sorted(df_posts['Top 5 values of Network.keyword'].dropna().unique().tolist())
        selected_rede = st.selectbox("Filtrar por Rede Social:", redes)

        filtered_posts = df_posts.copy()
        if selected_rede != "Todas":
            filtered_posts = filtered_posts[filtered_posts['Top 5 values of Network.keyword'] == selected_rede]

        top_n = st.slider("Número de Posts no gráfico (Top N):", 5, 30, 10)
        top_posts = filtered_posts.nlargest(top_n, 'Engajamento total')

        if not top_posts.empty:
            chart = alt.Chart(top_posts).mark_bar().encode(
                x=alt.X('Engajamento total', title='Engajamento Total'),
                y=alt.Y('Parlamentar', sort='-x', title='Parlamentar'),
                color=alt.Color('Top 5 values of Network.keyword', title='Rede Social'),
                tooltip=[
                    alt.Tooltip('Parlamentar'),
                    alt.Tooltip('Engajamento total', format=','),
                    alt.Tooltip('Top 5 values of Network.keyword', title='Rede'),
                    alt.Tooltip('Top 50 posts', title='Link do Post'),
                    alt.Tooltip('Message', title='Mensagem')
                ]
            ).properties(
                title=f"Top {top_n} Posts por Engajamento"
            ).interactive()

            st.altair_chart(chart, use_container_width=True)

            st.write("### Tabela dos Posts no Gráfico")
            st.dataframe(top_posts[['Date', 'Parlamentar', 'Top 5 values of Network.keyword', 'Engajamento total', 'Top 50 posts', 'Message']])
        else:
            st.info("Nenhum post encontrado com os filtros aplicados.")

# Rodar o app
if __name__ == '__main__':
    main()
