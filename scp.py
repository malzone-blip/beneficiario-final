import pandas as pd
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

t1=["2021-01-01",
"2021-06-01"]
t2=["2021-06-02",
"2021-12-01"]
t3=["2021-12-02",
"2022-06-01"]
t4=["2022-06-02",
"2022-12-01"]
t5=["2022-12-02",
"2022-12-31"]

list_dates=[t1,t2,t3,t4,t5]

list_dates

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/buscarProceso.cpe?sg=1")
    page.evaluate("""async () => { 
                document.querySelector("input[name='f_inicio']").value="2022-06-02"
                document.querySelector("input[name='f_fin']").value="2022-12-01"
                presentarProcesos(0);
                }""")
    
    html_table="table"
    df_colect=[]
    n_proce=0
    while "table" in html_table:
    # for i in range(1):
        html_table= page.locator("div[id='divProcesos']").inner_html()
        tables = pd.read_html(html_table,decimal=',', thousands='.')
        soup = BeautifulSoup(tabla, 'html.parser')
        df = tables[0]
        df_colect.append(df)
        page.evaluate("""async (n_proce) => { 
            var n_proce=n_proce
            presentarProcesos(n_proce);
                }""",n_proce)
        df.rename(columns=df.iloc[0], inplace=True)
        df.drop(df.index[0], inplace=True)
        links=[]
        for row in soup.find_all('tr'):
            try:
                url = row.find('a')['href']
                url_Sc="https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/"+url
                links.append(url_Sc)
            except:
                pass
        # df["links"]=links
        df["step"]=n_proce
        df["tmp"]=4
        n_proce=n_proce+20
        time.sleep(1)
        base_data= pd.read_csv("data/revision/review_proce.csv")
        concat_df= pd.concat([base_data,df])
        concat_df.to_csv("data/revision/review_proce.csv", index=False)
    browser.close()

 base_data= pd.read_csv("data/revision/review_proce.csv")

 # base_data[~["step"]]

 # base_data[]

 # base_data[~base_data.duplicated()]

list(base_data[base_data["Objeto del Proceso"].str.contains(
    "Estudio.*demanda|demanda.*estudio"
)]["Objeto del Proceso"])

base_data[base_data["Objeto del Proceso"].str.contains(
    "Estudio.*mercado|mercado.*estudio"
)]
