import streamlit as st
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import re

MAX_NIVEL = 5

def limpa_cnpj(cnpj):
    # Retira tudo que não for número
    return re.sub(r'\D', '', cnpj)

def consulta_cnpj_cnpja(cnpj):
    url = f"https://open.cnpja.com/office/{cnpj}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
        else:
            st.warning(f"CNPJA API retornou status {r.status_code}")
    except Exception as e:
        st.error(f"Erro na consulta CNPJA: {e}")
    return None

def consulta_cnpj_cnpjws(cnpj):
    url = f"https://publica.cnpj.ws/cnpj/{cnpj}"
    # URL atualizada para endpoint pública do cnpj.ws
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
        else:
            st.warning(f"CNPJ.ws API retornou status {r.status_code}")
    except Exception as e:
        st.error(f"Erro na consulta CNPJ.ws: {e}")
    return None

def extrai_socios(dados):
    socios = []
    if not dados:
        return socios

    if "qsa" in dados:
        for socio in dados["qsa"]:
            tipo = "pessoa_fisica" if socio.get("qualificacao", "").lower().find("sócio") != -1 or socio.get("qualificacao", "").lower().find("administrador") != -1 else "pessoa_juridica"
            socios.append({
                "nome": socio.get("nome", ""),
                "tipo": tipo,
                "cnpj": socio.get("cnpj", "")
            })
    elif "partners" in dados:
        for socio in dados["partners"]:
            tipo = "pessoa_fisica" if socio.get("is_individual", False) else "pessoa_juridica"
            socios.append({
                "nome": socio.get("name") or socio.get("nome") or "",
                "tipo": tipo,
                "cnpj": socio.get("cnpj_cpf") or socio.get("cnpj") or ""
            })
    elif "socios" in dados:
        for socio in dados["socios"]:
            socios.append({
                "nome": socio.get("nome", ""),
                "tipo": socio.get("tipo_socio", "pessoa_fisica"),
                "cnpj": socio.get("cnpj", "")
            })
    else:
        st.info("Nenhum campo esperado de sócios encontrado no JSON da API.")
    return socios

def busca_beneficiario_final(cnpj, nivel=1, max_nivel=MAX_NIVEL, visitados=None):
    if visitados is None:
        visitados = set()
    cnpj_limpo = limpa_cnpj(cnpj)
    if nivel > max_nivel or cnpj_limpo in visitados:
        return []
    visitados.add(cnpj_limpo)
    dados = consulta_cnpj_cnpja(cnpj_limpo)
    if dados is None:
        dados = consulta_cnpj_cnpjws(cnpj_limpo)
    if dados is None:
        st.error(f"Não foi possível obter dados do CNPJ: {cnpj_limpo}")
        return []
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

st.title("Consulta de Beneficiário Final - Cadeia Societária")

cnpj_input = st.text_input("Digite o CNPJ (com ou sem caracteres especiais)")

if st.button("Buscar"):
    if not cnpj_input or len(limpa_cnpj(cnpj_input)) != 14:
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
