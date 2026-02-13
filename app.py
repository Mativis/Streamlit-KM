import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import base64
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Visualizador de KM dos Veículos",
    page_icon="🚛",
    layout="wide"
)

# Título da aplicação
st.title("🚛 Visualizador de KM dos Veículos")
st.markdown("---")

# Função para extrair URL da imagem da coluna
def extract_image_url(url_string):
    """Extrai URL da imagem da string"""
    if pd.isna(url_string) or url_string == "":
        return None
    return str(url_string)

# Função para carregar e exibir imagem a partir da URL
def load_image_from_url(url):
    """Carrega imagem da URL"""
    try:
        response = requests.get(url, timeout=10)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        return None

# Função para processar dados da planilha
@st.cache_data
def load_data(uploaded_file):
    """Carrega e processa os dados da planilha"""
    try:
        # Carrega a planilha
        df = pd.read_excel(uploaded_file)
        
        # Cria nome completo combinando Nome e Sobrenome
        df['Nome'] = df['Nome'].fillna('')
        df['Sobrenome'] = df['Sobrenome'].fillna('')
        df['Nome Completo'] = df['Nome'].astype(str) + ' ' + df['Sobrenome'].astype(str)
        df['Nome Completo'] = df['Nome Completo'].str.strip()
        
        # Renomeia colunas para português mais amigável
        column_names = {
            'DateTime': 'Data/Hora',
            'Nome': 'Nome',
            'Sobrenome': 'Sobrenome',
            'Placa Veículo': 'Placa',
            'Número de Frota': 'Frota',
            'Qual a sua posição atual?': 'Status',
            'Qual a cidade em que esta aguardando o carregamento?': 'Cidade Carregamento',
            'Em qual cliente você está?': 'Cliente Carregamento',
            'Há quantas horas você esta aguardando para carregar?': 'Horas Aguardando Carregamento',
            'Em qual cidade você esta carregando?': 'Cidade Carregando',
            'Em qual cliente você está? 2': 'Cliente Carregando 2',
            'Qual a cidade de destino?': 'Destino',
            'Qual a cidade que você esta agora?': 'Cidade Atual',
            'Aguardando descarga em qual cidade?': 'Cidade Descarga',
            'Aguardando descarga em qual cliente?': 'Cliente Descarga',
            'Há quantas horas esta aguardando a descarga?': 'Horas Aguardando Descarga',
            'Está vazio em qual cidade?': 'Cidade Vazio',
            'Já tem carga?': 'Tem Carga',
            'Se sim, qual a cidade em que vai carregar?': 'Próxima Carga Cidade',
            'Se não tem carga, por favor informar há quantas horas esta aguardando?': 'Horas Aguardando Carga',
            'TIRAR FOTO DO KM ATUAL DO VEÍCULO': 'Foto KM'
        }
        
        # Renomeia colunas que existem
        for old_col, new_col in column_names.items():
            if old_col in df.columns:
                df.rename(columns={old_col: new_col}, inplace=True)
        
        # Processa URLs das imagens
        if 'Foto KM' in df.columns:
            df['Foto KM URL'] = df['Foto KM'].apply(extract_image_url)
        else:
            df['Foto KM URL'] = None
        
        # Preenche Status com 'Não informado' se necessário
        if 'Status' in df.columns:
            df['Status'] = df['Status'].fillna('Não informado')
        else:
            df['Status'] = 'Não informado'
        
        # Converte Data/Hora para datetime
        if 'Data/Hora' in df.columns:
            df['Data/Hora'] = pd.to_datetime(df['Data/Hora'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        return None

# Sidebar com botão de carregar dados e filtros
with st.sidebar:
    st.header("📁 Carregar Dados")
    
    # Botão para carregar dados
    uploaded_file = st.file_uploader(
        "Escolha o arquivo Excel", 
        type=['xlsx', 'xls'],
        help="Selecione a planilha com os dados dos veículos"
    )
    
    if uploaded_file is not None:
        if st.button("🔄 Carregar Dados", type="primary", use_container_width=True):
            with st.spinner("Carregando dados..."):
                df = load_data(uploaded_file)
                if df is not None:
                    st.session_state['data'] = df
                    st.session_state['filtered_data'] = df.copy()
                    st.success("✅ Dados carregados com sucesso!")
                    st.rerun()
    
    st.markdown("---")
    
    # Filtros (aparecem apenas se dados estiverem carregados)
    if 'data' in st.session_state:
        st.header("🔍 Filtros")
        df_filtered = st.session_state['data'].copy()
        
        # Filtro por Status
        if 'Status' in df_filtered.columns:
            status_options = ['Todos'] + sorted(df_filtered['Status'].dropna().unique().tolist())
            selected_status = st.selectbox("Status:", status_options, key='status_filter')
        else:
            selected_status = 'Todos'
        
        # Filtro por Placa
        if 'Placa' in df_filtered.columns:
            placas = ['Todas'] + sorted(df_filtered['Placa'].dropna().unique().tolist())
            selected_placa = st.selectbox("Placa do Veículo:", placas, key='placa_filter')
        else:
            selected_placa = 'Todas'
        
        # Filtro por Frota
        if 'Frota' in df_filtered.columns:
            frotas = ['Todas'] + sorted(df_filtered['Frota'].dropna().astype(str).unique().tolist())
            selected_frota = st.selectbox("Número da Frota:", frotas, key='frota_filter')
        else:
            selected_frota = 'Todas'
        
        # Filtro por Nome do Motorista
        if 'Nome Completo' in df_filtered.columns:
            motoristas = ['Todos'] + sorted(df_filtered['Nome Completo'].dropna().unique().tolist())
            selected_motorista = st.selectbox("Motorista:", motoristas, key='motorista_filter')
        else:
            selected_motorista = 'Todos'
        
        # Filtro por Data
        if 'Data/Hora' in df_filtered.columns and not df_filtered['Data/Hora'].isna().all():
            st.subheader("📅 Período")
            valid_dates = df_filtered['Data/Hora'].dropna()
            if not valid_dates.empty:
                min_date = valid_dates.min().date()
                max_date = valid_dates.max().date()
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Data inicial", min_date, min_value=min_date, max_value=max_date)
                with col2:
                    end_date = st.date_input("Data final", max_date, min_value=min_date, max_value=max_date)
            else:
                st.warning("Sem datas válidas para filtro")
                start_date = None
                end_date = None
        else:
            start_date = None
            end_date = None
        
        # Botão para aplicar filtros
        if st.button("🔍 Aplicar Filtros", type="primary", use_container_width=True):
            mask = pd.Series(True, index=df_filtered.index)
            
            if selected_status != 'Todos' and 'Status' in df_filtered.columns:
                mask &= (df_filtered['Status'] == selected_status)
            
            if selected_placa != 'Todas' and 'Placa' in df_filtered.columns:
                mask &= (df_filtered['Placa'] == selected_placa)
            
            if selected_frota != 'Todas' and 'Frota' in df_filtered.columns:
                mask &= (df_filtered['Frota'].astype(str) == selected_frota)
            
            if selected_motorista != 'Todos' and 'Nome Completo' in df_filtered.columns:
                mask &= (df_filtered['Nome Completo'] == selected_motorista)
            
            # Filtro de data
            if start_date and end_date and 'Data/Hora' in df_filtered.columns:
                mask &= (df_filtered['Data/Hora'].dt.date >= start_date)
                mask &= (df_filtered['Data/Hora'].dt.date <= end_date)
            
            st.session_state['filtered_data'] = df_filtered[mask]
            
            if len(st.session_state['filtered_data']) > 0:
                st.success(f"✅ {len(st.session_state['filtered_data'])} registro(s) encontrado(s)")
            else:
                st.warning("⚠️ Nenhum registro encontrado com os filtros selecionados")
        
        # Botão para limpar filtros
        if st.button("🗑️ Limpar Filtros", use_container_width=True):
            st.session_state['filtered_data'] = df_filtered.copy()
            st.success("✅ Filtros removidos")
            st.rerun()
        
        st.markdown("---")
        
        # Estatísticas rápidas
        st.header("📊 Estatísticas")
        total_registros = len(df_filtered)
        st.metric("Total de Registros", total_registros)
        
        if 'Foto KM URL' in df_filtered.columns:
            with_foto = df_filtered['Foto KM URL'].notna().sum()
            st.metric("Com Foto", with_foto)
        
        if 'Status' in df_filtered.columns:
            status_count = df_filtered['Status'].value_counts().to_dict()
            st.write("**Distribuição por Status:**")
            for status, count in status_count.items():
                st.write(f"- {status}: {count}")

# Área principal
if 'data' in st.session_state:
    # Usa dados filtrados se disponíveis, senão usa todos
    if 'filtered_data' in st.session_state:
        df_display = st.session_state['filtered_data']
    else:
        df_display = st.session_state['data'].copy()
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(["📸 Visualização de Fotos", "📋 Tabela de Dados", "📍 Distribuição por Status"])
    
    with tab1:
        if len(df_display) > 0:
            st.subheader(f"📸 Fotos do KM ({len(df_display)} registros)")
            
            # Grid de fotos
            cols_per_row = 3
            for idx in range(0, len(df_display), cols_per_row):
                cols = st.columns(cols_per_row)
                for col_idx, (_, row) in enumerate(df_display.iloc[idx:idx+cols_per_row].iterrows()):
                    with cols[col_idx]:
                        with st.container(border=True):
                            # Informações do veículo
                            nome_completo = row.get('Nome Completo', 'N/A')
                            placa = row.get('Placa', 'N/A')
                            frota = row.get('Frota', 'N/A')
                            status = row.get('Status', 'N/A')
                            data_hora = row.get('Data/Hora', 'N/A')
                            
                            st.markdown(f"**👤 {nome_completo}**")
                            st.markdown(f"🚘 Placa: {placa} | Frota: {frota}")
                            st.markdown(f"📌 Status: {status}")
                            st.markdown(f"🕒 {data_hora}")
                            
                            # Foto do KM
                            if pd.notna(row.get('Foto KM URL')):
                                try:
                                    img = load_image_from_url(row['Foto KM URL'])
                                    if img:
                                        st.image(img, caption=f"KM do Veículo - {placa}", use_container_width=True)
                                    else:
                                        st.warning("❌ Erro ao carregar imagem")
                                except Exception as e:
                                    st.error(f"Erro: {e}")
                            else:
                                st.info("📷 Sem foto disponível")
                            
                            # Botão para abrir link em nova aba
                            if pd.notna(row.get('Foto KM URL')):
                                st.markdown(f"[🔗 Abrir imagem em nova aba]({row['Foto KM URL']})")
        else:
            st.info("Nenhum registro encontrado com os filtros selecionados")
    
    with tab2:
        st.subheader("📋 Tabela de Dados")
        
        # Colunas para exibir na tabela
        base_columns = ['Data/Hora', 'Nome Completo', 'Placa', 'Frota', 'Status']
        available_base = [col for col in base_columns if col in df_display.columns]
        
        # Adiciona colunas de localização se existirem
        location_columns = ['Cidade Atual', 'Destino', 'Cidade Carregamento', 'Cidade Descarga', 'Cidade Vazio']
        available_location = [col for col in location_columns if col in df_display.columns]
        
        # Colunas de tempo de espera
        time_columns = ['Horas Aguardando Carregamento', 'Horas Aguardando Descarga', 'Horas Aguardando Carga']
        available_time = [col for col in time_columns if col in df_display.columns]
        
        # Colunas para mostrar
        columns_to_show = available_base + available_location[:2] + available_time[:1]
        
        # Adiciona coluna de link para foto
        if 'Foto KM URL' in df_display.columns:
            df_display['Link Foto'] = df_display['Foto KM URL'].apply(
                lambda x: f'🔗 Link' if pd.notna(x) else '❌ Sem foto'
            )
            columns_to_show.append('Link Foto')
        
        st.dataframe(
            df_display[columns_to_show],
            use_container_width=True,
            height=500,
            column_config={
                "Link Foto": st.column_config.LinkColumn("Foto", display_text="🔗 Abrir")
            }
        )
        
        # Botão para download dos dados filtrados
        if not df_display.empty:
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download dados filtrados (CSV)",
                data=csv,
                file_name=f"dados_veiculos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with tab3:
        if 'Status' in df_display.columns and not df_display['Status'].empty:
            st.subheader("📍 Distribuição por Status")
            
            # Gráfico de barras com a distribuição por status
            status_dist = df_display['Status'].value_counts().reset_index()
            status_dist.columns = ['Status', 'Quantidade']
            
            st.bar_chart(status_dist.set_index('Status'))
            
            # Tabela com detalhes por status
            st.subheader("Detalhamento por Status")
            for status in df_display['Status'].unique():
                if pd.notna(status):
                    status_df = df_display[df_display['Status'] == status]
                    
                    with st.expander(f"📌 {status} ({len(status_df)} veículos)"):
                        # Informações resumidas
                        col1, col2, col3 = st.columns(3)
                        
                        if status == "Aguardando carregamento":
                            with col1:
                                if 'Cidade Carregamento' in status_df.columns:
                                    st.metric("Cidades", status_df['Cidade Carregamento'].nunique())
                            with col2:
                                if 'Cliente Carregamento' in status_df.columns:
                                    st.metric("Clientes", status_df['Cliente Carregamento'].nunique())
                        
                        elif status == "Aguardando descarga":
                            with col1:
                                if 'Cidade Descarga' in status_df.columns:
                                    st.metric("Cidades", status_df['Cidade Descarga'].nunique())
                            with col2:
                                if 'Cliente Descarga' in status_df.columns:
                                    st.metric("Clientes", status_df['Cliente Descarga'].nunique())
                        
                        elif status == "Vazio":
                            with col1:
                                if 'Cidade Vazio' in status_df.columns:
                                    st.metric("Cidades", status_df['Cidade Vazio'].nunique())
                            with col2:
                                if 'Tem Carga' in status_df.columns:
                                    st.metric("Com Carga", status_df['Tem Carga'].value_counts().get('Sim', 0))
                        
                        with col3:
                            st.metric("Total Veículos", len(status_df))
                        
                        # Lista de veículos neste status
                        display_cols = []
                        if 'Nome Completo' in status_df.columns:
                            display_cols.append('Nome Completo')
                        if 'Placa' in status_df.columns:
                            display_cols.append('Placa')
                        if 'Frota' in status_df.columns:
                            display_cols.append('Frota')
                        
                        # Adiciona colunas de cidade disponíveis
                        city_cols = [col for col in status_df.columns if 'Cidade' in col or 'Cliente' in col][:3]
                        display_cols.extend(city_cols)
                        
                        if display_cols:
                            st.dataframe(status_df[display_cols], use_container_width=True)
        else:
            st.info("Sem dados de status para exibir")

else:
    # Mensagem inicial quando não há dados
    st.info("👈 Por favor, carregue a planilha usando o botão no menu lateral para começar a visualização.")
    
    # Exemplo de como usar
    with st.expander("ℹ️ Como usar"):
        st.markdown("""
        ### 📋 Instruções de uso:
        
        1. **Clique no botão "Browse files"** no menu lateral esquerdo
        2. **Selecione o arquivo Excel** contendo os dados dos veículos
        3. **Clique em "Carregar Dados"** para importar a planilha
        4. **Use os filtros** para encontrar registros específicos
        5. **Visualize as fotos** do KM dos veículos na aba principal
        6. **Explore as outras abas** para ver tabelas e estatísticas
        
        ### 📊 Funcionalidades:
        
        - ✅ Visualização das fotos do KM em grid
        - ✅ Filtros por status, placa, frota, motorista e data
        - ✅ Tabela interativa com todos os dados
        - ✅ Estatísticas e distribuição por status
        - ✅ Download dos dados filtrados
        """)

# Rodapé
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        Desenvolvido para visualização de KM dos veículos 🚛
    </div>
    """,
    unsafe_allow_html=True
)