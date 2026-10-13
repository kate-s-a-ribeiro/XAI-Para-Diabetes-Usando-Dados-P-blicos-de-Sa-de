import pandas as pd     # primeiro, importamos pandas para leitura de csv
import matplotlib.pyplot as plt
import ast


# vamos estar lendo ambos os CSV e salvando-os
data2013 = pd.read_csv('./py/IC/ArquivosCsv/PNS_2013.csv', index_col=False, sep=';', encoding='utf-8')
#data2019 = pd.read_csv('./py/IC/ArquivosCsv/pns2019.csv', index_col=False, sep=',') # enquanto o separador do de 2013 é ';', o de 2019 é só ','

# vermos se está tudo certo
#print(data2013.describe())
#print(data2019.describe())

# printar as informações
print(data2013.info())  # dataframe com 222385 linhas, 1000 colunas, com 10 tipos int e object(990)
#print(data2019.info())  # dataframe com 293726 linhas, 1087 colunas, com 1078 tipos float e 9 int
'''
selecao1 = (data2019['S066'] >= 20.0)

print(data2019[selecao1])
print(data2019['S066'].unique())
print(data2019[selecao1]['V0001'].unique())'''

# vamos fazer um resumo do dataframe
# começaremos por 2013

resumo2013 = pd.DataFrame({
    "Tipo": data2013.dtypes,
    "Nulos": data2013.isnull().sum(),
    "% nulos": data2013.isnull().mean(),
    "únicos": data2013.nunique()
})

print(resumo2013)
resumo2013.to_csv("./py/IC/ArquivosCSV/resumo_2013.csv", index=False, sep=';')

print("Tamo aqui 1")

# temos que centenas de colunas que deveriam ter valores numéricos na verdade tem valores "object", isso é, string
# vamos tentar converter
# para isso, vamos criar um series com as colunas do tipo objeto
colunas_obj = data2013.select_dtypes(include="object").columns

print("Tamo aqui 2")

# vamos checar se tem valores que dão erro ao tentar converter para numérico
'''for col in data2013.columns:
    invalidos = data2013.loc[pd.to_numeric(data2013[col], errors='coerce').isna(), col].unique()
    if len(invalidos) > 0:
        print(col, invalidos[:10])  # mostra até 10 valores problemáticos'''
        
# diversos valores problemáticos de cada coluna apareceram
# isso significa que existem valores inteiros e existem valores float (com casa decimal)
# analisando algumas das colunas, temos que esses valores não são errados
# as colunas em questão parecem todas ter haver com renda (reais admite casa decimal), peso (kg admite casa decimal) e etc
# então vamos fazer o seguinte
# para cada coluna nas colunas do data2013
for col in data2013.columns:
    # vamos criar uma série que vai ser as colunas do data2013, com os valores vazios substituídos para NA e as vírgulas das strings sendo substituídas por .
    serie = (
        data2013[col]
        .replace(r'^\s*$', pd.NA, regex=True)
        .astype("string")
        .str.replace(",", ".", regex=False)
    )

    # converte para valores numéricos (float)
    num = pd.to_numeric(serie, errors='coerce')

    # se os valores numéricos (sem contar o NA) forem inteiros, substitui o tipo para inteiro
    if (num.dropna() % 1 == 0).all():
        data2013[col] = num.astype('Int64')
    else:   # se não for, deixa float
        data2013[col] = num
        
        
print("Tamo aqui 3")

# vamos salvar esse novo csv
data2013.to_csv("./py/IC/ArquivosCSV/pns2013alterado.csv", index=False, sep=';', encoding='utf-8')

print("Tamo aqui 4")

# printar resumo desse novo
resumo2013 = pd.DataFrame({
    "Tipo": data2013.dtypes,
    "Nulos": data2013.isnull().sum(),
    "% nulos": data2013.isnull().mean(numeric_only=True),
    "unicos": data2013.nunique()
})

print(resumo2013)
resumo2013.to_csv("./py/IC/ArquivosCSV/resumo_2013alterado.csv", index=False, sep=';')

print("Tamo aqui 5")

# muito bem, agora temos um resumo
# vamos analisar as estatísticas do dataset transposto
# isso é importante porque o dataset é grande
# assim, vamos parar de analisar cada coluna e passar a analisar cada amostra
pd.set_option('display.max_rows', None)
estatistica = data2013.describe().T
estatistica.to_csv("./py/IC/ArquivosCSV/estatisticas2013prealteracao.csv", index=False, sep=';')
print(estatistica)

#pd.reset_option('display.max_rows')

print("Tamo aqui 6")

# vamos, agora, fazer o uso do IQR, Interquartile Range, intervalo interquartil
# que é uma medida de dispersão estatística que vai nos ajudar a detectar os outliers automaticamente
# a ideia é que os outliers sejam aqueles abaixo do limite inferior (1° quartil - 1.5*IQR) ou superior ao limite superior (2° quartil + 1.5*IQR)
outliers_num = {}
outliers_cat = {}

# vamos ler o arquivo com a tipagem de cada variável
# a primeira coluna vamos nomear "código" (o código da variavel) e a segunda "tipo" (0 para categórico, 1 para numérico)
tipagem = pd.read_csv('./py/IC/ArquivosCSV/2013 PNS/TIPAGEM_DICIONARIO_2013.csv', index_col=False, sep=';', dtype={'tipo': str}, encoding='utf-8')

# a coluna cod_especial contém uma string do tipo "[99]", "[]" ou "[99, 00]"
# então vamos passar a string pelo ast.literal_eval, que parsa a string como uma expressão literal
# assim, se não for NA, a gente vai colocar a lista como a string tá, e se for, a gente vai deixar vazio
tipagem['cod_especial'] = tipagem["cod_especial"].apply(lambda x: ast.literal_eval(x) if pd.notna(x) else [])

# vamos fazer um dicionário que tenha para cada código um tipo
mapa_tipos = dict(zip(tipagem['codigo'], tipagem['tipo']))  # no entanto, o tipo vai ser string
codespecial = dict(zip(tipagem['codigo'], tipagem['cod_especial']))
mini = dict(zip(tipagem['codigo'], tipagem['min']))
maxi = dict(zip(tipagem['codigo'], tipagem['max']))
descricao = dict(zip(tipagem['codigo'], tipagem['desc_var']))

#print(mapa_tipos)

for col in data2013.columns:
    tipo = mapa_tipos.get(col) # vamos pegar o tipo de cada coluna (vai estar em string)
    codigoespecial = codespecial.get(col, [])
    desc = descricao.get(col)
    
    if desc is None or pd.isna(desc):
        desc = "Descricao nao encontrada!"
    
    if tipo is not None and tipo.isdigit():
        tipo = int(tipo)    # se não for nulo, converte pra int
    else:
        print(f"ERRO! Coluna {col} tá bugada, por que???")
        continue
    
    if codigoespecial is not None and isinstance(codigoespecial, list):
        # Converte cada código especial para número
        codigoespecial = [
            int(x) for x in codigoespecial
            if str(x).strip().isdigit()
        ]
        colunafiltrada = data2013.loc[~data2013[col].isin(codigoespecial), col]
        # lógica: data2013.loc[data2013[col].isin(codigoespecial), col] vai checar na coluna valores que contenham qualquer um dos códigos especiais, desde que seja não nulo
        # caso haja portanto, seja codigoespecial = [88, 00] para aquela coluna, vai vai retornar os valores que contenham 00 ou 88
        # o ~ serve para inverter
        # então, ao invés de pegar o 88 ou 00, ele pega tudo MENOS o 88 e 00 (ou seja, só os valores válidos!)
    else:
        colunafiltrada = data2013[col]
        
    minimo_esperado = mini.get(col)
    maximo_esperado = maxi.get(col)
    
    
    if not pd.isna(minimo_esperado) and minimo_esperado is not None:
        minimo_esperado = float(minimo_esperado)
    if not pd.isna(maximo_esperado) and maximo_esperado is not None:
        maximo_esperado = float(maximo_esperado)
        
    
    
    if tipo == 1:
        colunafiltrada = colunafiltrada.dropna()    # vamos tirar os valores NA
        
        # se a coluna ficar vazia:
        if colunafiltrada.empty:
            outliers_num[col] = {
                "col": pd.NA,
                "q1": pd.NA,
                "q3": pd.NA,
                "iqr": pd.NA,
                "limite_inf": pd.NA,
                "limite_sup": pd.NA,
                "qtd_outliers": 0,
                "pct_outliers": 0,
                "qtd_outliers_duvidoso": 0,
                "pct_outliers_duvidoso": 0
        }
            continue
        
        q1 = colunafiltrada.quantile(0.25)
        q3 = colunafiltrada.quantile(0.75)
        iqr = q3 - q1
            
        limite_inf = q1 - 1.5*iqr
        limite_sup = q3 + 1.5*iqr
        
        if minimo_esperado is None or pd.isna(minimo_esperado):
            minimo_esperado = limite_inf
            print("MINIMO ESPERADO NAO ENCONTRADO!")
        if maximo_esperado is None or pd.isna(maximo_esperado):
            maximo_esperado = limite_sup
            print("MAXIMO ESPERADO NAO ENCONTRADO!")
            
        qtd_fora_dominio = ((colunafiltrada < minimo_esperado) | (colunafiltrada > maximo_esperado)).sum()
        
        if pd.isna(iqr) or iqr == 0:
            qtd_duvidoso = 0
        else:
            qtd_duvidoso = ((colunafiltrada < limite_inf) | (colunafiltrada > limite_sup)).sum()
        
        n_validos = colunafiltrada.notna().sum()
        
        if n_validos != 0:
            pct_outliers_certeza = qtd_fora_dominio / colunafiltrada.notna().sum() * 100
            pc_outliers_duvidoso = qtd_duvidoso / colunafiltrada.notna().sum() * 100
        else:
            pct_outliers_certeza = 0
            pc_outliers_duvidoso = 0
            
        
        outliers_num[col] = {
            "variavel": col,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "limite_inf": limite_inf,
            "limite_sup": limite_sup,
            "valores_fora_dominio": qtd_fora_dominio,
            "qtd_outliers_icr": qtd_duvidoso,
            "pct_valores_fora_dominio": pct_outliers_certeza,
            "pct_outliers_ic": pc_outliers_duvidoso
        }
        
        if qtd_fora_dominio == 0:
            continue
        else:
            print(f"COLUNA: {col} É NUMÉRICA!  |  MÉDIA: {colunafiltrada.mean()}  |  MEDIANA: {colunafiltrada.median()}  |  DESVIO: {colunafiltrada.std()}  |  LIMITE INFERIOR: {limite_inf}  |  MINIMO ESPERADO: {minimo_esperado}  |  LIMITE SUPERIOR: {limite_sup}  |  MAXIMO ESPERADO: {maximo_esperado}  | QNT. OUTLIERS: {qtd_fora_dominio}  |  QNT. OULIERS DUVIDOSOS: {qtd_duvidoso}\n")
        
        
    if tipo == 0:
            colunafiltrada = colunafiltrada.dropna()    # vamos tirar os valores NA
            frequencias = colunafiltrada.value_counts(normalize=True)
            
            # vamos definir como "categoria rara" as categorias com < 5% de frequência
            categorias_raras = frequencias[frequencias < 0.05].index
            
            raras_porcentagem = frequencias[categorias_raras]
            
            qtd_fora_dominio = ((colunafiltrada < minimo_esperado) | (colunafiltrada > maximo_esperado)).sum()
            
            n_validos = colunafiltrada.notna().sum()
            if n_validos !=0:
                pct_foradominio = qtd_fora_dominio / n_validos * 100
            else:
                pct_foradominio = 0

            if raras_porcentagem.empty:
                print(f"COLUNA: {col} É CATEGÓRICA!  | FREQUENCIAS: {frequencias.to_list()}  |  RARAS: {raras_porcentagem.to_list()}\n")
                  
            outliers_cat[col] = {
                "descricao": desc,
                "limite_inf": minimo_esperado,
                "limite_sup": maximo_esperado,
                "valores_fora_dominio": qtd_fora_dominio,
                "pct_fora_dominio": pct_foradominio,
                "frequencias": frequencias.to_list(),
                "porcentagem_raras": raras_porcentagem.to_list()
            }
            
    
# assim, outliers = uma series com a quantidade de outliers em cada coluna

print("Tamo aqui 7")

outliers_num = pd.DataFrame(outliers_num).T
outliers_num.to_csv('./py/IC/ArquivosCSV/2013 PNS/OUTLIERS_NUMERICOS_2013.csv', index=False, sep=';', encoding='utf-8')
outliers_num = outliers_num.sort_values(
    "pct_valores_fora_dominio",
    ascending=False
)

outliers_cat = pd.DataFrame(outliers_cat).T
outliers_cat.to_csv('./py/IC/ArquivosCSV/2013 PNS/OUTLIERS_CATEGORICOS_2013.csv', index=False, sep=';', encoding='utf-8')

#print(outliers_df.info())
print(outliers_num)
print(outliers_cat)
import numpy as np

# Seleciona apenas pessoas com resposta válida para diabetes e renda
dados_filtrados = data2013[
    data2013['Q030'].isin([1, 3]) &
    data2013['VDF002'].notna()
].copy()

# Cria os grupos
renda_sim = dados_filtrados.loc[
    dados_filtrados['Q030'] == 1, 'VDF002'
]

renda_nao = dados_filtrados.loc[
    dados_filtrados['Q030'] == 3, 'VDF002'
]

# Figura
fig, ax = plt.subplots(figsize=(8, 5))

# Boxplot
box = ax.boxplot(
    [renda_sim, renda_nao],
    positions=[1, 2],
    widths=0.45,
    patch_artist=True,
    showfliers=False
)

# Cores dos boxes
cores = ['#4472C4', '#70AD47']

for patch, cor in zip(box['boxes'], cores):
    patch.set_facecolor(cor)
    patch.set_alpha(0.65)

# Jitter para os pontos
np.random.seed(42)

x_sim = np.random.normal(1, 0.06, size=len(renda_sim))
x_nao = np.random.normal(2, 0.06, size=len(renda_nao))

ax.scatter(
    x_sim,
    renda_sim,
    color='#1F4E79',
    alpha=0.20,
    s=10,
    edgecolors='none'
)

ax.scatter(
    x_nao,
    renda_nao,
    color='#375623',
    alpha=0.20,
    s=10,
    edgecolors='none'
)

# Configuração dos eixos
ax.set_xticks([1, 2])
ax.set_xticklabels(['Sim', 'Não'])

ax.set_xlabel('Presença de diabetes')
ax.set_ylabel('Renda (VDF002)')
ax.set_title('Distribuição da renda segundo a presença de diabetes')

# Grade apenas no eixo Y
ax.yaxis.grid(True, linestyle='--', alpha=0.25)
ax.set_axisbelow(True)

# Remove bordas superiores e direita
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.show()


dados_filtrados = data2013[
    data2013['Q030'].isin([1, 3]) &
    data2013['VDF002'].notna()
].copy()

np.random.seed(42)

# Jitter no eixo X
x = dados_filtrados['Q030'].astype(float).to_numpy()
x_jitter = x + np.random.normal(0, 0.06, size=len(x))

fig, ax = plt.subplots(figsize=(8, 5))

ax.scatter(
    x_jitter,
    dados_filtrados['VDF002'],
    color='#2563EB',
    alpha=0.25,
    s=12,
    edgecolors='none'
)

ax.set_xticks([1, 3])
ax.set_xticklabels(['Sim', 'Não'])

ax.set_xlabel('Presença de diabetes')
ax.set_ylabel('Renda (VDF002)')
ax.set_title('Distribuição da renda segundo a presença de diabetes')

ax.yaxis.grid(True, linestyle='--', alpha=0.25)
ax.set_axisbelow(True)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.show()

import ast
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================
# 1. CONFIGURAÇÃO VISUAL
# ============================================================

sns.set_theme(style="whitegrid", context="notebook")

PALETA = {
    "sociodemograficas": "#4472C4",
    "saude": "#70AD47",
    "comportamento": "#ED7D31"
}

# ============================================================
# 2. INFORME AQUI OS CÓDIGOS DAS VARIÁVEIS
# ============================================================

variaveis = {
    "sociodemograficas": {
        "Sexo": "C006",
        "Idade": "C008",
        "Raça/cor": "C009",
        "Escolaridade": "D009",
        "Renda domiciliar": "VDF002",
        "Situação de trabalho": "E014",
        "Situação de domicílio": "A001",
        "Estado civil": "C011"
    },

    "saude": {
        "Hipertensão autorreferida": "Q002",
        "Artrite/reumatismo": "Q079",
        "Câncer": "Q120",
        "Saúde autorreferida": "N001"
    },

    "comportamento": {
        "Atividade física nos últimos 7 dias": "P035",
        "Tabagismo": "P05402",
        "Uso de álcool": "P028"
    }
}

# Exemplo de preenchimento:
# "Sexo": "C006"
#
# Use os códigos reais presentes em data2013.columns.
# Não deixe None nas variáveis que deseja plotar.

# ============================================================
# 3. PREPARAÇÃO DOS CÓDIGOS ESPECIAIS
# ============================================================

def obter_codigos_especiais(coluna):
    codigos = codespecial.get(coluna, [])

    if not isinstance(codigos, (list, tuple, set)):
        return []

    resultado = []

    for codigo in codigos:
        try:
            valor = float(str(codigo).strip().replace(",", "."))
            if np.isfinite(valor):
                resultado.append(valor)
        except (ValueError, TypeError):
            pass

    return resultado


# ============================================================
# 4. LIMPEZA DAS VARIÁVEIS
# ============================================================

def preparar_variavel(coluna):
    """
    Retorna a série limpa e os limites utilizados.

    Remove:
    - valores ausentes;
    - códigos especiais;
    - valores abaixo do mínimo esperado;
    - valores acima do máximo esperado.

    Os limites são inclusivos: valores iguais ao mínimo ou
    máximo esperado são mantidos.
    """

    if coluna not in data2013.columns:
        raise KeyError(
            f"A variável '{coluna}' não existe em data2013."
        )

    serie = data2013[coluna].copy()

    # Converte para numérico quando possível.
    # Valores que não puderem ser convertidos viram NaN.
    serie = pd.to_numeric(serie, errors="coerce")

    # Exclui códigos especiais.
    especiais = obter_codigos_especiais(coluna)

    if especiais:
        serie = serie.mask(serie.isin(especiais))

    # Recupera os limites esperados do dicionário.
    minimo = mini.get(coluna)
    maximo = maxi.get(coluna)

    if minimo is not None and pd.notna(minimo):
        minimo = float(minimo)
        serie = serie.mask(serie < minimo)

    if maximo is not None and pd.notna(maximo):
        maximo = float(maximo)
        serie = serie.mask(serie > maximo)

    # Remove os valores ausentes após a filtragem.
    serie = serie.dropna()

    return serie, minimo, maximo


# ============================================================
# 5. CLASSIFICAÇÃO DAS VARIÁVEIS
# ============================================================

# Variáveis contínuas ou discretas com muitos valores distintos.
# Serão representadas por histogramas.
NUMERICAS_CONTINUAS = {
    "Idade",
    "Renda domiciliar",
    "IMC"
}

# Contagens são numéricas, mas costumam ser mais fáceis de
# interpretar em barras quando têm poucos valores possíveis.
'''NUMERICAS_CONTAGEM = {
    "Contagem de comorbidades",
    "Contagem de incapacidades"
}
'''

# As demais serão representadas por gráficos de barras.
# Se necessário, altere estas listas de acordo com a codificação
# real e a natureza das variáveis na sua base.


# ============================================================
# 6. FUNÇÃO PARA GERAR UM GRÁFICO
# ============================================================

def plotar_variavel(nome, coluna, grupo, ax):
    cor = PALETA[grupo]

    serie, minimo, maximo = preparar_variavel(coluna)

    if serie.empty:
        ax.text(
            0.5, 0.5,
            "Nenhum valor válido após a filtragem",
            ha="center", va="center",
            transform=ax.transAxes
        )
        ax.set_title(nome)
        ax.set_axis_off()
        return

    # --------------------------------------------------------
    # Histogramas e boxplots para variáveis contínuas
    # --------------------------------------------------------
    if nome in NUMERICAS_CONTINUAS:

        valores = serie.astype(float)

        sns.histplot(
            valores,
            bins="auto",
            color=cor,
            edgecolor="white",
            ax=ax
        )

        ax.set_ylabel("Número de pessoas")
        ax.set_xlabel(nome)

        # Média e mediana como referências.
        mediana = valores.median()
        ax.axvline(
            mediana,
            color="#C00000",
            linestyle="--",
            linewidth=1.8,
            label=f"Mediana: {mediana:.2f}"
        )
        ax.legend(frameon=False)

    # --------------------------------------------------------
    # Barras para contagens de comorbidades/incapacidades
    # --------------------------------------------------------

    # --------------------------------------------------------
    # Barras para variáveis categóricas
    # --------------------------------------------------------
    else:

        frequencias = serie.value_counts(
            normalize=True,
            sort=True
        ) * 100

        sns.barplot(
            x=frequencias.index.astype(str),
            y=frequencias.values,
            color=cor,
            ax=ax
        )

        ax.set_xlabel(nome)
        ax.set_ylabel("Percentual de pessoas (%)")

        # Percentuais acima das barras.
        ax.bar_label(
            ax.containers[0],
            fmt="%.1f%%",
            padding=2,
            fontsize=8
        )

        # Evita sobreposição quando há muitas categorias.
        if len(frequencias) > 5:
            ax.tick_params(axis="x", rotation=45)

    ax.set_title(f"{nome}\n(n = {len(serie):,})")
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ============================================================
# 7. GERAÇÃO AUTOMÁTICA DOS GRÁFICOS
# ============================================================

def gerar_graficos():
    resumo = []

    for grupo, dicionario in variaveis.items():

        # Considera somente variáveis com código informado.
        selecionadas = {
            nome: codigo
            for nome, codigo in dicionario.items()
            if codigo is not None and str(codigo).strip() != ""
        }

        if not selecionadas:
            print(
                f"Nenhuma variável configurada para o grupo: {grupo}"
            )
            continue

        nomes = list(selecionadas.keys())

        # Duas colunas de gráficos por figura.
        n_colunas = 2
        n_linhas = math.ceil(len(nomes) / n_colunas)

        fig, eixos = plt.subplots(
            n_linhas,
            n_colunas,
            figsize=(14, 4.5 * n_linhas),
            squeeze=False
        )

        fig.suptitle(
            grupo.replace("_", " ").title(),
            fontsize=16,
            fontweight="bold",
            y=1.01
        )

        for i, nome in enumerate(nomes):
            coluna = selecionadas[nome]
            ax = eixos.flat[i]

            try:
                plotar_variavel(nome, coluna, grupo, ax)

                serie, minimo, maximo = preparar_variavel(coluna)

                resumo.append({
                    "grupo": grupo,
                    "variavel": nome,
                    "codigo": coluna,
                    "n_validos": len(serie),
                    "minimo_observado": (
                        serie.min() if len(serie) else np.nan
                    ),
                    "mediana": (
                        serie.median() if len(serie) else np.nan
                    ),
                    "maximo_observado": (
                        serie.max() if len(serie) else np.nan
                    ),
                    "minimo_esperado": minimo,
                    "maximo_esperado": maximo
                })

            except Exception as erro:
                ax.set_title(nome)
                ax.text(
                    0.5, 0.5,
                    f"Erro ao gerar gráfico:\n{erro}",
                    ha="center", va="center",
                    transform=ax.transAxes,
                    wrap=True
                )
                ax.set_axis_off()

        # Oculta os eixos que sobraram.
        for i in range(len(nomes), len(eixos.flat)):
            eixos.flat[i].set_visible(False)

        plt.tight_layout()
        plt.show()

    return pd.DataFrame(resumo)


# Executa quando os códigos das variáveis forem preenchidos.
resumo_graficos = gerar_graficos()

print(resumo_graficos)


'''
# podemos, ainda, fazer uma análise exploratória dessas estatísticas:
analiseestatistica = pd.DataFrame({
    "Tipo": data2013.dtypes,
    "Numero Nulos": data2013.isnull().sum(),
    "Porcentagem Nulos": data2013.isnull().mean()*100,
    "Média": data2013['mean'],
    "Mediana": data2013['50%'],
    "Desvio Padrão": data2013['std'],
    "Minimo": estatistica['min'],
    "Máximo": estatistica['max'],
    "25%": estatistica['75%'],
    "75%": estatistica['25%'],
    "N° Unicos": estatistica.nunique(),
    "IQR": estatistica['75%'] - estatistica['25%']  # IQR = 3° quartil - 1° quartil
})


print("Tamo aqui 9")

analiseestatistica.to_csv("./py/IC/ArquivosCSV/analiseestatistica2013prealteracao.csv", index=False, sep=';')
print(analiseestatistica)
'''
