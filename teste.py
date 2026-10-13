import pandas as pd
import re


#df = pd.read_excel('./py/IC/ArquivosCsv/Dicionario-de-variaveis_PNS-2013.xlsx', skiprows=[1, 2, 3, 4, 60, 61, 225, 247, 248, 296, 373, 504, 521, 635, 684, 999, 1316, 1496, 1497, 1709, 1966, 2297, 3130, 3392, 3670, 3792, 4007, 4056, 4065])
df = pd.read_excel('./py/IC/ArquivosCsv/Dicionario-de-variaveis_PNS-2013.xlsx', header=None, skiprows=[0, 1, 2, 3, 59, 60, 224, 246, 247, 295, 372, 503, 520, 634, 683, 998, 1315, 1495, 1496, 1708, 1965, 2296, 3129, 3391, 3669, 3791, 4006, 4055, 4064])

print(df.tail(50))

def extrair_intervalo(texto):
    if pd.isna(texto):
        return None, None

    texto = str(texto).strip()

    # Procura padrões como:
    # 000 a 999
    # 1 a 10
    # 01 até 99
    # 000 - 999
    padrao = r'^\s*(\d+)\s*(?:a|até|-)\s*(\d+)\s*$'

    match = re.match(padrao, texto, flags=re.IGNORECASE)

    if match:
        minimo = int(match.group(1))
        maximo = int(match.group(2))
        return minimo, maximo

    return None, None

def verificar_letra_na_variavel(codigo_alvo):
    # nomeamos as colunas
    # 0 = código
    # 1 = descrição da variável
    # 2 = respostas
    # 3 = descrição da resposta
    df.columns = ['codigo', 'desc_var', 'resposta', 'desc_resp']
    
    # filtramos pelo código desejado, enquanto só tem uma única coluna com código
    filtro_codigo = df[df['codigo'] == codigo_alvo].copy()
    
    # vamos pegar a descrição da variável
    desc_var_series = filtro_codigo['desc_var'].dropna()

    if desc_var_series.empty:
        desc_var = "Sem descrição"
    else:
        desc_var = desc_var_series.iloc[0]
    
    # vamos dar fill pra caso não faça isso nativamente
    df['codigo'] = df['codigo'].ffill()

    # filtramos pelo código desejado, agora pra pegar todas as colunas com código pelo fill
    filtro_codigo = df[df['codigo'] == codigo_alvo].copy()

    if filtro_codigo.empty:
        return f"Código '{codigo_alvo}' não encontrado.", 0, -1, "NÃO ENCONTRADO"


    
    # inicializamos a variável como categórica e tentamos achar motivos para ser numérica
    tipo = "Categórica"
    codespecial = []
    descricao = []

    # condição para ser numérica: checar se há "a" em qualquer célula da coluna de resposta (Coluna 3)
    # .astype(str) evita erro com nulos; case=False ignora maiúsculas
    intervalos = filtro_codigo['resposta'].apply(extrair_intervalo)

    if intervalos.map(lambda x: x[0] is not None).any():
        tipo = "Numérica"
        
    # depois disso, vamos checar os valores especiais de cada variável
    # os valores especiais serão:
    lista_naos = ["0", "00", "000", "0000", "99", "999", "9999", "88", "888"]
    # além de valores vazios (mas nem todo valor vazio é um valor especial, assim como nem todo valor "0" é um valor especial!)
    
#    resposta_str = filtro_codigo['resposta'].astype(str).str.strip() #pra ser mais rápido
    
    linhas_procuradas = filtro_codigo[filtro_codigo['resposta'].isna() | (filtro_codigo['resposta'].astype(str).str.strip().eq("")) | (filtro_codigo['resposta'].astype(str).str.strip().isin(lista_naos))]
    
    min_valor = None
    max_valor = None
    intervalo_encontrado = False

    
    for valor in filtro_codigo['resposta']:
        minimo_intervalo, maximo_intervalo = extrair_intervalo(valor)

        if minimo_intervalo is not None:
            min_valor = minimo_intervalo
            max_valor = maximo_intervalo
            intervalo_encontrado = True
            
            if not filtro_codigo[filtro_codigo['desc_var'].astype(str).str.contains('0', na=False)].empty:
                min_valor = min_valor - 1
            
            break
    
    if not linhas_procuradas.empty:
        for _, linha in linhas_procuradas.iterrows():
            resposta = linha['resposta']
            nulo = pd.isna(resposta)
            resposta_str_linha = str(resposta).strip()
            texto_col4 = str(linha['desc_resp']).lower()
            
            
            condicao_0 = ((resposta_str_linha == "0" or resposta_str_linha == "00" or resposta_str_linha == "000" or resposta_str_linha == "0000" or resposta_str_linha == "" or nulo == True or not resposta_str_linha) and "não" in texto_col4)
            condicao_resto = (resposta_str_linha in lista_naos and resposta_str_linha != "0")
            
            # valores vazios ou com 0 = checa se contém "não" no lado
            # caso contrário, basta ser um dos demais valores da lista_naos
            if (condicao_0 or condicao_resto):
                if not nulo:
                    codespecial.append(resposta_str_linha)
                else:
                    continue
                
                
                descricao.append(texto_col4)
                
    if not intervalo_encontrado:
        respostas = pd.to_numeric(filtro_codigo['resposta'], errors='coerce')
        
        codespecial_num = []
        
        for codigo in codespecial:
            try:
                codespecial_num.append((float(codigo)))
            except (ValueError, TypeError):
                pass
            
        respostas_validas = respostas[respostas.notna() & ~respostas.isin(codespecial_num)]
        
        if not respostas_validas.empty:
            min_valor = respostas_validas.min()
            max_valor = respostas_validas.max()
                
          
        
    # tira o ffill
    df['codigo'] = df['codigo'].mask(df['codigo'].shift() == df['codigo'])

    # retorno final
    if tipo == "Numérica":
        return 1, codespecial, descricao, min_valor, max_valor, desc_var    # 1 = numérica
    else:
        return 0, codespecial, descricao, min_valor, max_valor, desc_var    # 0 = categórica
    
    
    

ds = []


for cod in range(4067):
    if(not pd.isna(df.iloc[cod, 0])):
        tipo, codespecial, descricao, min, max, desc = verificar_letra_na_variavel(df.iloc[cod, 0])
        
        ds.append({
            'codigo': df.iloc[cod, 0].upper(),
            'tipo': tipo,
            'cod_especial': codespecial,
            'descricao': descricao,
            'min': min,
            "max": max,
            "desc_var": desc
        })
    else:
        continue

    
dataframe = pd.DataFrame(ds)

dataframe.to_csv('./py/IC/ArquivosCSV/2013 PNS/TIPAGEM_DICIONARIO_2013.csv', index=False, sep=';', encoding='utf-8')
    
print(ds)
print(dataframe)
print(dataframe.info())
