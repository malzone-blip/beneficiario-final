import streamlit as st
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

MAX_NIVEL = 5

def consulta_cnpj_cnpja(cnpj):
    url = f"https://open.cnpja.com/office/{cnpj}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return None

def consulta_cnpj_cnpjws(cnpj):
    url = f"https://www.cnpj.ws/{cnpj}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return None

def extrai_socios(dados):
    socios = []
    if not dados:
        return socios
    if "partners" in dados:
        for p in dados["partners"]:
            socio = {
                "nome": p.get("name") or p.get("nome") or "",
                "tipo": "pessoa_fisica" if p.get("is_individual") else "pessoa_juridica",
                "cnpj": p.get("cnpj_cpf") or p.get("cnpj") or ""
            }
            socios.append(socio)
    elif "socios" in dados:
        for p in dados["socios"]:
            socio = {
                "nome": p.get("nome"),
                "tipo": p.get("tipo_socio"),
                "cnpj": p.get("cnpj")
            }
            socios.append(socio)
    return socios

def busca_beneficiario_final(cnpj, nivel=1, max_nivel=MAX_NIVEL, visitados=None):
    if visitados is None:
        visitados = set()
    cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
    if nivel > max_nivel or cnpj_limpo in visitados:
        return []
    visitados.add(cnpj_limpo)
    dados = consulta_cnpj_cnpja(cnpj_limpo) or consulta_cnpj_cnpjws(cnpj_limpo)
    socios = extrai_socios(dados)
    resultados = []
    for socio in socios:
        if socio['tipo'] == 'pessoa_fisica':
            resultados.append({'cnpj': cnpj_limpo, 'socio': socio, 'nivel': nivel})
        elif socio['tipo'] == 'pessoa_juridica' and socio.get('cnpj'):
            resultados.extend(busca_beneficiario_final(socio['cnpj'], nivel + 1, max_nivel, visitados))
    return resultados

def gera_pdf(dados):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Relatório de Beneficiário Final")
    c.setFont("Helvetica", 12)
    y -= 40

    for item in dados:
        texto = f"Nível {item['nivel']} - Nome: {item['socio']['nome']}"
        c.drawString(40, y, texto)
        y -= 20
        if y < 40:
            c.showPage()
            y = height - 40

    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# Streamlit UI

st.title("Consulta de Beneficiário Final - Cadeia Societária")

cnpj_input = st.text_input("Digite o CNPJ (somente números)")

if st.button("Buscar"):
    if not cnpj_input or len(cnpj_input) < 14:
        st.error("Informe um CNPJ válido com 14 dígitos.")
    else:
        with st.spinner("Consultando a cadeia societária..."):
            resultados = busca_beneficiario_final(cnpj_input)
        if resultados:
            st.success(f"Encontrados {len(resultados)} beneficiário(s) final(is)")
            for item in resultados:
                st.write(f"Nível {item['nivel']} - Nome: {item['socio']['nome']}")
            
            if st.button("Gerar relatório PDF"):
                pdf_bytes = gera_pdf(resultados)
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name="relatorio_beneficiario_final.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("Nenhum beneficiário final encontrado.")
