import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.title("Consulta de Beneficiário Final - Cadeia Societária Local")

def unificar_arquivos(pasta):
    arquivos = [f for f in os.listdir(pasta) if f.startswith("K3241.K03200Y0.D50913.SOCIOCSV")]
    dfs = []
    for arq in arquivos:
        caminho = os.path.join(pasta, arq)
        df = pd.read_csv(caminho, sep='|', dtype=str, encoding='latin1', on_bad_lines='skip')
        dfs.append(df)
    df_final = pd.concat(dfs, ignore_index=True)
    df_final.columns = map(str.lower, df_final.columns)
    return df_final

def busca_cadeia(df, cnpj, visitados=None, nivel=1, max_nivel=5):
    if visitados is None:
        visitados = set()
    cnpj = str(cnpj).zfill(14)
    if nivel > max_nivel or cnpj in visitados:
        return []
    visitados.add(cnpj)
    socios = df[df['cnpj'] == cnpj]
    resultados = []
    for _, socio in socios.iterrows():
        socio_id = socio['cpf_cnpj_socio']
        nome = socio['nome_socio']
        tipo = socio['tipo_socio'].lower()
        if tipo.startswith('pessoa física'):
            resultados.append({'nivel': nivel, 'nome': nome, 'identificacao': socio_id})
        else:
            resultados.extend(busca_cadeia(df, socio_id, visitados, nivel+1, max_nivel))
    return resultados

def gera_pdf(dados):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Relatório Beneficiário Final")
    c.setFont("Helvetica", 12)
    y -= 40
    for item in dados:
        texto = f"Nível {item['nivel']} - Nome: {item['nome']} - ID: {item['identificacao']}"
        c.drawString(40, y, texto)
        y -= 20
        if y < 40:
            c.showPage()
            y = height - 40
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

pasta_arquivos = st.text_input("Informe o diretório onde os arquivos SOCIOCSV estão localizados")

if st.button("Unificar e carregar base"):
    if not os.path.isdir(pasta_arquivos):
        st.error("Diretório inválido.")
    else:
        with st.spinner("Unificando arquivos..."):
            df_qsa = unificar_arquivos(pasta_arquivos)
        st.success(f"Base carregada com {df_qsa.shape[0]} registros.")
        st.session_state['df_qsa'] = df_qsa

if 'df_qsa' in st.session_state:
    cnpj = st.text_input("Digite o CNPJ para busca final (somente números)")
    if st.button("Buscar beneficiários"):
        if len(cnpj) != 14 or not cnpj.isdigit():
            st.error("Informe um CNPJ válido com 14 dígitos.")
        else:
            with st.spinner("Buscando beneficiários finais..."):
                resultado = busca_cadeia(st.session_state['df_qsa'], cnpj)
            if resultado:
                for item in resultado:
                    st.write(f"Nível {item['nivel']} - {item['nome']} - {item['identificacao']}")
                if st.button("Gerar relatório PDF"):
                    pdf_bytes = gera_pdf(resultado)
                    st.download_button("Download PDF", pdf_bytes, file_name="beneficiarios_finais.pdf", mime="application/pdf")
            else:
                st.info("Nenhum beneficiário final encontrado.")

