import pandas as pd
import time
import random
from tqdm import tqdm

inicio = time.perf_counter()

# +
# df_csv=pd.read_csv("companiasactivas.csv")

# +
# df_csv["RUC"]=df_csv["RUC"].astype(str)
# df_csv["RUC"]=df_csv["RUC"].apply(lambda x: str(x).split('.')[0])
# df_csv["EXPEDIENTE"]=df_csv["EXPEDIENTE"].apply(lambda x: str(x).split('.')[0])
# # Añadimos el cero a los Ruc que no poseen 
# df_csv["RUC"]=df_csv["RUC"].apply(lambda x: "0" + x if len(x) == 12 else x )

# +
# Guardamos los Rucs que si constan en la base de compañias
# base_directorio=pd.DataFrame({"RUC":df_csv["RUC"].unique()})

# +
# int_groups=len(base_directorio)//250
# -

for i in tqdm(range(10+1)):
    # Espere un tiempo aleatorio entre 5 y 10 segundos
    time.sleep(random.uniform(10, 15))
    exec(open("Scrap_SC.py").read())

# +
fin = time.perf_counter()

tiempo_ejecucion = fin - inicio

tiempo_ejecucion_min=tiempo_ejecucion/60

# Muestra el tiempo de ejecución en segundos
print(f'Tiempo Total de ejecución: {tiempo_ejecucion_min:.2f} minutos')
