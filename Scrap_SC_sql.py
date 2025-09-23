import pandas as pd
from playwright.sync_api import sync_playwright
import threading
import time
import pandas as pd
import re
import time
import random
import pickle
from datetime import datetime
import json
import asyncio
import time
from playwright.async_api import async_playwright
import playwright.async_api as async_api
import pytesseract
import requests
from io import BytesIO
from PIL import Image
from time import sleep
from tqdm import tqdm
import os
import traceback
import warnings
import requests, zipfile, io
warnings.filterwarnings('ignore')
import datetime
import locale
from datetime import date
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
inicio = time.perf_counter()
# Selecionamos la ubicación en la que se encuentra instalada la libreria Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import pymysql
from sqlalchemy import create_engine


def optain_data(path="Today"):

    if path!= "Today":
    # Si el argumento path no es igual a "Today", abrimos el archivo en la ruta especificada y cargamos los datos en formato JSON
        
        with open(path,'r', encoding="utf8") as f:
            data = json.loads(f.read())
    elif path=="Today":
        
    # Si el argumento path es igual a "Today", descargamos los datos del mes actual en formato JSON a través de una solicitud HTTP
    
        current_month_n=date.today().month
        current_year_n=date.today().year
        urljson=f'https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/download?type=json&year={current_year_n}&month={current_month_n}&method=all'
        urlj=urljson
        rj= requests.get(urlj)
        zj = zipfile.ZipFile(io.BytesIO(rj.content))
        name_json=zj.namelist()[0]
        data = json.load(zj.open(name_json))   
        
        
    df = pd.json_normalize(data, record_path =['releases'])
    df["ruc_contratante"]=df["buyer.id"].str.extract("EC-RUC-(\d+)")
    def awar_id(x):
        try:
            return x[0]['suppliers'][0]['id']
        except:
            pass
    df["awar_id"]=df['awards'].apply(awar_id)
    extra_ruc = r"(?:ID-|EC-RUC-)(\d+)"
    df["RUC"]=df["awar_id"].str.extract(extra_ruc )
    def awar_name(x):
        try:
            return x[0]['suppliers'][0]['name']
        except:
            pass
    df["nombre"]=df['awards'].apply(awar_name)
    def awar_amount(x):
        try:
            return x[0]['value']['amount']
        except:
            pass
    df["monto"]=df['awards'].apply(awar_amount)
    df["tag"]=df["tag"].astype(str)
    df_notag=df[df["tag"].str.contains("award")]
    select_df=df_notag[["nombre","RUC","monto","ocid","buyer.name","buyer.id","ruc_contratante","date","tender.procurementMethodDetails",
                 'tender.description']]
    select_df_name=select_df.rename(columns={'buyer.name':'contratante', 'buyer.id':'id_conrtatante','date':'fecha','tender.description':'obj_contrato'})
    return select_df_name

proveedores=optain_data()

proveedores.head(2)

# +
# proveedores=pd.read_csv("all_proveedores_21_22.csv",converters={'RUC': str})

# +
# proveedores=proveedores.rename(columns={"ruc":"RUC"})
# -

proveedores["RUC"]=proveedores["RUC"].apply(lambda x: x+"001" if x[-3:] != "001" else x )
proveedores["RUC"]=proveedores["RUC"].apply(lambda x: "0" + x if len(x) == 12 else x )

len(proveedores["RUC"].unique())

# +
# base_directorio=proveedores

# +
# df = pd.read_excel("directorio_companias.xlsx", skiprows=4)

# +
# %%time
# base_directorio=pd.read_csv("data/companias/companiasactivas.csv",converters={'RUC': str})
url_excel_companis='https://mercadodevalores.supercias.gob.ec/reportes/excel/directorio_companias.xlsx'
r = requests.get(url_excel_companis)

base_directorio= pd.read_excel(r.content, skiprows=4,converters={'RUC': str})
# -

base_directorio["RUC"]=base_directorio["RUC"].astype(str)
base_directorio["RUC"]=base_directorio["RUC"].apply(lambda x: str(x).split('.')[0])
base_directorio["EXPEDIENTE"]=base_directorio["EXPEDIENTE"].apply(lambda x: str(x).split('.')[0])
base_directorio["RUC"]=base_directorio["RUC"].apply(lambda x: "0" + x if len(x) == 12 else x )
base_directorio["RUC"]=base_directorio["RUC"].apply(lambda x: x+"001" if x[-3:] != "001" else x )

base_directorio_T= base_directorio.drop_duplicates(subset="RUC")

# +
# Comparamos Si existe el Ruc en la Base de Compañias 
in_compani=[]

def find_df(x):
    if base_directorio_T["RUC"].isin([x]).any():
        in_compani.append(x)
    elif base_directorio_T["EXPEDIENTE"].isin([x]).any():
        ruc_find=base_directorio_T[base_directorio_T["EXPEDIENTE"]==x]["RUC"].iloc[0]
        in_compani.append(ruc_find)    
    else:
        pass
      
for i in proveedores["RUC"].unique():
    find_df(i)
# -

# Guardamos los Rucs que si constan en la base de compañias
base_directorio=pd.DataFrame({"RUC":in_compani})

# Test 5 procesos
base_directorio=base_directorio[0:5]
base_directorio

# +
# len(base_directorio["RUC"].unique())

# +
# base_directorio.to_csv("all_proveedores_21_22.csv", index=False)

# +
# Link de la pagina de supercias
linkpaht="https://appscvsconsultas.supercias.gob.ec/consultaCompanias/societario/busquedaCompanias.jsf"

find_by="RUC"
# Generamos la carpeta en donde se alamacenaran los datos (de existir no se genera)
# Establecemos el nombre de archivo pkl en el cual se guardaran los datos y los errores 
folder_save="data/accionistas"
# if not os.path.exists(folder_save):
    # os.makedirs(folder_save)
# Base de datos en la que se almacenan los datos del Scrap
ubi_save=os.path.join(folder_save, "data_accionistas.csv")
# Base de datos en la que se almacenan los errores del scrap
ubi_save_errors=os.path.join(folder_save, "data_errors.pkl")


##### Analisis por lotes
# Establecemos el numero de compañias que se analizaran cada vez que se ejecute el código
n_reviews=250


# +
# Conectamos con MySQL
# name_data_base_sql="test_sql"
# usuario="root"
# contrasena=""
# host="127.0.0.1"
# table_name="data_accionistas"
# engine = create_engine(f'mysql+mysqlconnector://{usuario}:{contrasena}@{host}/{name_data_base_sql}')


# +
# Cargamos las bases de datos y los errores (si no se tienen no se carga)
try:
    # Base de datos en la que se almacenan los datos del Scrap
    # base_data= pd.read_csv(ubi_save) 
    base_data = pd.read_sql_table(table_name, engine, index_col=None)
    base_data[f"{find_by}_empresa"]=base_data[f"{find_by}_empresa"].astype(str)
    base_data[f"{find_by}_empresa"]=base_data[f"{find_by}_empresa"].apply(lambda x: "0" + x if len(x) == 12 else x )
    # De la base de datos que ya se encuentra extrayeron los datos, buscamos la ultima compañia analizada 
    # y a partir de aquella se continuara con las siguientes 50 compañias 
    # base_data["EXPEDIENTE_empresa"]=base_data["EXPEDIENTE_empresa"].astype(int)
    # base_data=base_data.sort_values(by="EXPEDIENTE_empresa",ascending=True)
    # base_data["EXPEDIENTE_empresa"]=base_data["EXPEDIENTE_empresa"].astype(str)
    
    last_ruc=base_data.tail(1)[f"{find_by}_empresa"].iloc[0]

    last_search=base_directorio[base_directorio[find_by]==last_ruc].index[0]

    to_scrap=base_directorio[last_search+1:last_search+1+n_reviews]
except:
    pass

try:
    # Base de datos en la que se almacenan los datos de errores del  Scrap
    base_errors= pd.read_pickle(ubi_save_errors) 
    base_errors["errores"]=base_errors["errores"].apply(lambda x: str(x).split('.')[0])
except:
    base_errors=pd.DataFrame({"errores":[]})
    pass


# +
# len(base_data[f"{find_by}_empresa"].unique())
# -

# Selecionamos las copañias que no se pudieron analizar por errores  
# y le sumamos la base con las compañias nuavas por analizar 
# Esto nos da el listado de nuevas empresas por analizar 
try:
    companies=list(base_errors["errores"])+list(to_scrap[find_by])
except:
    companies=list(base_directorio[find_by][0:n_reviews])

# +
## Eliminar alguna compañia ya analizada
# ruc_delet="1790016919001"
# base_data_delet=base_data[base_data['ruc_empresa']!=ruc_delet]
# base_data_delet.to_pickle(ubi_save)  
# -

try:
    # Se Almacenaran la lista de empresas ya analizadas y las que faltan de analizar 
    scrap_done=[]
    list_companies_not=[]

    # Filtramos las empresas que ya han sido analizadas 
    def find_df(x):
        if base_data[f'{find_by}_empresa'].isin([x]).any():
            scrap_done.append(x)
        else:
            list_companies_not.append(x)
    for i in companies:
        find_df(i)
    # Eliminamos repetidos
    list_companies=list_companies_not
    sin_repetir = []
    for elemento in list_companies:
        if elemento not in sin_repetir:
            sin_repetir.append(elemento)
            
    list_companies=sin_repetir
except:
    list_companies=companies
    # Eliminamos repetidos
    list_companies=companies
    sin_repetir = []
    for elemento in list_companies:
        if elemento not in sin_repetir:
            sin_repetir.append(elemento)
            
    list_companies=sin_repetir
    pass

# +
# len(list_companies)
# -

if len(list_companies)==0:
        # Comparamos Si existe el Ruc en la Base de Compañias 
    not_scrap=[]
    def find_df(x):
        if base_data["RUC_empresa"].isin([x]).any():
            pass
        else:
            not_scrap.append(x)
            pass

    for i in base_directorio["RUC"]:
        find_df(i)
    list_companies=not_scrap


# +
# len(list_companies)
# -

def review(lista,df_list):
    in_base_directori=[]
    no_in_directori=[]
    # Filtramos las empresas que ya han sido analizadas 
    def find_df(x):
        if df_list.isin([x]).any():
            in_base_directori.append(x)
        else:
            no_in_directori.append(x)

    for i in lista:
        find_df(i)
    return in_base_directori,no_in_directori


async def run(playwright,list_companies):
    # Si todas las empresas de la lista  ya han sido analizadas no se ejecuta el codigo 
    if len(list_companies)==0:
        return print("Lista de compañias ya revisadas")
    try:
        # Se ejecuta cuado el codigo ya ha analizado compnias previamente
        # añadiendo las nuevas companias analizadas
        df_accionistas=[base_data]
    except:
        # Primera vez  que se ejecuta el codigo 
        df_accionistas=[]
    # almacenamos el ruc de la compañias con errores
    errors=[]
    # Usamos el buscador por defecto
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()
    # Cargamos la pagina por analizar
    await page.goto(linkpaht)
    # Creamos un loop for que permita nalizar cada compañia del listado definido 
    for company in tqdm(list_companies):
        # Capturamos aquellas compañias que generen error para poder analizadarlas luego
        try:
            
            time.sleep(1)
            try:
                await page.evaluate("""async () => { 
                document.querySelector("label[for='frmBusquedaCompanias:tipoBusqueda:1']").click()
                }""")
            except:
                await page.goto(linkpaht)
                # print("Se dio un Error al pulsar el RUC")
                time.sleep(2)
                await page.evaluate("""async () => { 
                document.querySelector("label[for='frmBusquedaCompanias:tipoBusqueda:0']").click()
                }""")
                await page.evaluate("""async () => { 
                document.querySelector("label[for='frmBusquedaCompanias:tipoBusqueda:1']").click()
                }""")
            time.sleep(1)
            # Tipeamos el ruc de la compañia
            await page.keyboard.type(company, delay=200)
            time.sleep(1)
            try:
                await page.keyboard.press("Enter")
                time.sleep(1)
            # Optenemos la url de la imagen del captcha
           
                link=  await page.evaluate("""async () => { 
                   var link=document.querySelector("img[id='frmBusquedaCompanias:captchaImage']").src
                   return link
                    }""")
            except Exception as e:
                await page.goto(linkpaht)
                # print("#####SE REPITIO por QUR NO ENtoncto")
                time.sleep(1)
                await page.evaluate("""async () => { 
            document.querySelector("label[for='frmBusquedaCompanias:tipoBusqueda:0']").click()
            }""")
                await page.evaluate("""async () => { 
            document.querySelector("label[for='frmBusquedaCompanias:tipoBusqueda:1']").click()
            }""") 
                await page.locator("input[id='frmBusquedaCompanias:parametroBusqueda_input']").fill("")
                time.sleep(2)
                await page.keyboard.type(company, delay=300)
                time.sleep(2)
                await page.keyboard.press("Enter")
                time.sleep(3)
                link=  await page.evaluate("""async () => { 
                   var link=document.querySelector("img[id='frmBusquedaCompanias:captchaImage']").src
                   return link
                    }""")
                
                # traceback.print_exc()
               
            
            #  OCR a la iamgen del captcha
            response = requests.get(link)
            image = Image.open(BytesIO(response.content))
            code = pytesseract.image_to_string(image)
            # Tipeamos el resultado del analisis del captcha
            await page.locator("input[id='frmBusquedaCompanias:captcha']").fill("")
            await page.locator("input[id='frmBusquedaCompanias:captcha']").type(code, delay=100);
            text_aler=  await page.evaluate("""async () => { 
            var text_aler=document.querySelector("div[id='frmBusquedaCompanias:msgBusquedaCompanias'] div")
            return text_aler
            }""")
            if type(text_aler) is str:
                errors.append(company)
                await page.goto(linkpaht)
                continue
            #######################
            time.sleep(2)
            # Accedemos al menu de Accionistas
            
            
            await page.locator("a[id='frmMenu:menuAccionistas']").click()
            time.sleep(2)
            # Analisis del captcha de la ventana de Accinistas
            captcha_2=await page.locator("img[id='frmCaptcha:captchaImage']").get_attribute("src")
            response_2 = requests.get(captcha_2)
            image_2 = Image.open(BytesIO(response_2.content))
            code_2 = pytesseract.image_to_string(image_2)
            # Si el captcha analizado nos arroja numeros procedemos a llenar el captcha 
            # De lo contrario no se ha presentado captcha alguno(no se analiza el captcha)
            if bool(re.match(r'^\d+$',code_2)):
                await page.locator("input[id='frmCaptcha:captcha']").fill("")
                await page.locator("input[id='frmCaptcha:captcha']").type(code_2, delay=200);
                text_aler_2=  await page.evaluate("""async () => { 
                var text_aler_2=document.querySelector("div[id='frmCaptcha:msgCaptcha'] div")
                return text_aler_2
                }""")
                if type(text_aler_2) is str:
                    await page.goto(linkpaht)
                    time.sleep(1)
                    continue
            # Establecemos que se desplieguen todos los accionistas de la compañia 
            check = "block"
            while "block" in check:
                check=await page.evaluate("""async () => { 
                style=document.querySelectorAll(".ui-dialog")[0].getAttribute("style")
                return style
                }""")
            await page.click("select")   
            for i in range(0,8):
                # time.sleep(0.5)
                await page.keyboard.press('ArrowDown')
            time.sleep(1)
            await page.keyboard.press("Enter")
            time.sleep(1)
            # Comprobamos si se han cargado todos los accionistas
            check = "block"
            while "block" in check:
                check=await page.evaluate("""async () => { 
                style=document.querySelectorAll(".ui-dialog")[0].getAttribute("style")
                return style
                }""")
            # Extraemos la tabla completa de accionistas 
            html_table=await page.locator("div[id='frmInformacionCompanias:tblAccionistas'] .ui-datatable-tablewrapper").inner_html()
            # Transformamos la tabla en un dataframe pandas
            tables = pd.read_html(html_table,decimal=',', thousands='.')
            df = tables[0]
            # Agregamos el ruc de la compañia a cada accinista
            df[f"{find_by}_empresa"]=company
            df_accionistas.append(df)
            print(df)
            try :
                base_data = pd.read_sql_table(table_name, engine, index_col=None)
                # base_data[f"{find_by}_empresa"]=base_data[f"{find_by}_empresa"].astype(str)
                # base_data[f"{find_by}_empresa"]=base_data[f"{find_by}_empresa"].apply(lambda x: "0" + x if len(x) == 12 else x )
                # concat_df_shrs = pd.concat([base_data,df])
                # concat_df_shrs[f"{find_by}_empresa"]=concat_df_shrs[f"{find_by}_empresa"].astype(str)
                # # concat_df_shrs.to_csv(ubi_save, index=False)
                # concat_df_shrs.to_sql(table_name, engine, if_exists='replace', index=False)
            
            except:
               
                # df.to_sql(table_name, engine, if_exists='replace', index=False)
                 pass
                 
        
            # De la base de datos que ya se encuentra extrayeron los datos, buscamos la ultima compañia analizada 
            # regresamos a la pantalla inicial para analizar otra compañia
            await page.locator("button[id='frmNuevaConsulta:j_idt16']").click()
            time.sleep(1)
        except Exception as e:
            # traceback.print_exc()
            # Captamos los errores
            errors.append(company)
            await page.goto(linkpaht)
            # print("No realizado",errors)
            continue
    # conctamos las base ya analizada con los nuevos analisis
    # concat_df_shrs = pd.concat(df_accionistas)
    # concat_df_shrs[f"{find_by}_empresa"]=concat_df_shrs[f"{find_by}_empresa"].astype(str)
    # Guardamos la nueva base
    # concat_df_shrs.to_csv(ubi_save, index=False)
    # Data frame de errores
    errors_df=pd.DataFrame({"errores":errors})
    # Guardamos los errores
    # errors_df.to_pickle(ubi_save_errors) 
    print("Numero de Errores: ", len(errors_df))
    # Cerramos el buscador 
    await browser.close()
    return errors_df,df_accionistas

async def main():
    async with async_playwright() as playwright:
       capture_ok_error,df_scrpa= await run(playwright,list_companies)
    return capture_ok_error,df_scrpa
error,df_scrap=asyncio.run(main())

df_lista=[df_scrap]

print("Corrigiendo Errores",error)

while len(error)>0:
    async def main():
        async with async_playwright() as playwright:
           capture_ok_error,df_scrpa= await run(playwright,list(error["errores"]))
        return capture_ok_error,df_scrpa
    error,df_scrap=asyncio.run(main())
    df_lista.append(df_scrap)

# +
# print("Print Lista Completa")
# print(df_lista)

# +
# concat_df_shrs = pd.concat(df_lista)

# +
# print("Print Concat")
# print(concat_df_shrs)

# +
# print(concat_df_shrs)

# +
# base_data=concat_df_shrs 

# +
# base_data["Identificación"]=base_data["Identificación"].apply(lambda x: "0" + x if len(x) == 12 else x )
# base_data_compani=base_data[(base_data["Identificación"].apply(lambda x: len(x) > 11) )&
#           (base_data["NacionalidadFilter by Nacionalidad"]=="ECUADOR")]
# in_companis=review(base_data_compani["Identificación"].unique(),base_directorio_T["RUC"])[0]
# # print("Compañias que son accionistas: ",len(in_companis))
# to_scrap=review(in_companis,base_data[f'{find_by}_empresa'])[1]
# print("A Scrap: ",len(to_scrap))

# async def main():
#     async with async_playwright() as playwright:
#        capture_ok_error,df_scrpa= await run(playwright,list_companies)
#     return capture_ok_error,df_scrpa
# error,df_scrap=asyncio.run(main())

# df_lista=[df_scrap]

# while len(error)>0:
#     async def main():
#         async with async_playwright() as playwright:
#            capture_ok_error,df_scrpa= await run(playwright,list(error["errores"]))
#         return capture_ok_error,df_scrpa
#     error,df_scrap=asyncio.run(main())
#     df_lista.append(df_scrap)

# +
# concat_df_shrs = pd.concat(df_lista)

# +
# print(concat_df_shrs )

# +
fin = time.perf_counter()

tiempo_ejecucion = fin - inicio

tiempo_ejecucion_min=tiempo_ejecucion/60

# Muestra el tiempo de ejecución en segundos
print(f'Tiempo de ejecución: {tiempo_ejecucion_min:.2f} minutos')
# -



# +
# len(base_directorio["RUC"].unique())

# +
# len(review(list_companies,base_data[f"{find_by}_empresa"])[0])

# +
# len(review(base_directorio["RUC"],base_data[f"{find_by}_empresa"])[1])

# +
# len(base_data[base_data[f"{find_by}_empresa"].isin(base_directorio["RUC"].unique())]["RUC_empresa"].unique())

# +
# if len(base_data[f"{find_by}_empresa"].unique())>len(base_directorio["RUC"].unique()):
#     base_data["Identificación"]=base_data["Identificación"].apply(lambda x: "0" + x if len(x) == 12 else x )
#     base_data_compani=base_data[(base_data["Identificación"].apply(lambda x: len(x) > 11) )&
#               (base_data["NacionalidadFilter by Nacionalidad"]=="ECUADOR")]
#     in_companis=review(base_data_compani["Identificación"].unique(),base_directorio_T["RUC"])[0]
#     # print("Compañias que son accionistas: ",len(in_companis))
#     to_scrap=review(in_companis,base_data[f'{find_by}_empresa'])[1]
#     print("A Scrap: ",len(to_scrap))
#     async def main():
#         async with async_playwright() as playwright:
#             await run(playwright,to_scrap)
#     asyncio.run(main())


# +
# df_whit_com=base_data[base_data['Identificación'].isin(in_companis)]
# comp_whit_com=base_data[base_data['Identificación'].isin(in_companis)]["RUC_empresa"]
# df_whit_compa_more=base_data[base_data[f"{find_by}_empresa"].isin(comp_whit_com)]
# -



# +
# position=3
# finf_l1=df_whit_com.iloc[[position]]
# display(finf_l1)
# id_posit=df_whit_com.iloc[[position]].iloc[0].iloc[0]

# finf_l2=df_whit_com[df_whit_com["RUC_empresa"]==id_posit]
# display(finf_l2)

# id_posit_l2=finf_l2.iloc[0].iloc[0]
# id_posit_l2

# finf_l3=df_whit_com[df_whit_com["RUC_empresa"]==id_posit_l2]
# display(finf_l3)

# id_posit_l3=finf_l3.iloc[0].iloc[0]
# id_posit_l3

# finf_l4=df_whit_com[df_whit_com["RUC_empresa"]==id_posit_l3]
# display(finf_l4)

# id_posit_l5=finf_l3.iloc[1].iloc[0]
# id_posit_l5

# finf_l5=df_whit_com[df_whit_com["RUC_empresa"]==id_posit_l5]
# display(finf_l5)

# id_posit_l6=finf_l4.iloc[0].iloc[0]
# id_posit_l6

# finf_l6=df_whit_com[df_whit_com["RUC_empresa"]==id_posit_l6]
# display(finf_l6)

# +
# df_whit_com=df_test=df_whit_com[df_whit_com["Identificación"].isin(df_whit_com["RUC_empresa"])]


# +
# df_whit_com

# +
# from pyvis.network import Network
# col_bg='#131013'
# col_proc='#f6a341'
# col_entAwar='red'
# col_ent='#4FA5E3'
# # Crea una red de grafos
# net = Network(notebook=True, height='400px', width='100%', bgcolor=col_bg, font_color="white", directed=True)

# for i in df_whit_com[f"{find_by}_empresa"].unique():
#         net.add_node(i, label='Node 1',color=col_proc)

# for i in df_whit_com["Identificación"].unique():
#     net.add_node(i, label='Node 1',color=col_proc)

# for i,k in zip(df_whit_com[f"{find_by}_empresa"],df_whit_com["Identificación"]):  
#         net.add_edge(i, k)
# display(net.show("accinistas_conetc.html"))

# +
# from pyvis.network import Network
# col_bg='#131013'
# col_proc='#f6a341'
# col_entAwar='red'
# col_ent='#4FA5E3'
# # Crea una red de grafos
# net = Network(notebook=True, height='400px', width='100%', bgcolor=col_bg, font_color="white", directed=True)

# for i in df_whit_com[f"{find_by}_empresa"].unique():
#         net.add_node(i, label='Node 1',color="red")

# for i in df_whit_com["Identificación"].unique():
#     net.add_node(i, label='Node 1',color=col_proc)

# for i,k in zip(df_whit_com[f"{find_by}_empresa"],df_whit_com["Identificación"]):  
#         net.add_edge(i, k)
# display(net.show("accinistas_conetc.html"))
# -


