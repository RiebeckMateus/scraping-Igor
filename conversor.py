import json
import pandas as pd
import openpyxl

with open('as.json', 'r', encoding='utf-8') as file:
    dados = json.load(file)

# print(dados[0])

linhas = []

for jogo in dados:
    for jogo_id, jogo_info in jogo.items():
        time_casa = jogo_info['time_casa']
        time_fora = jogo_info['time_fora']
        
        # print(time_casa)
        
        for ocorrencia in jogo_info['ocorrencias_time_casa']:
            linha = {
                'jogo': jogo_id,
                'time': time_casa,
                'ocorrencia': ocorrencia['ocorrencia'],
                'tempo_ocorrencia': ocorrencia['tempo_ocorrencia'],
                'como': 'time da casa',
                'detalhes': ocorrencia['detalhes']
            }
            linhas.append(linha)
        
        for ocorrencia in jogo_info['ocorrencias_time_fora']:
            linha = {
                'jogo': jogo_id,
                'time': time_fora,
                'ocorrencia': ocorrencia['ocorrencia'],
                'tempo_ocorrencia': ocorrencia['tempo_ocorrencia'],
                'como': 'time de fora',
                'detalhes': ocorrencia['detalhes']
            }
            linhas.append(linha)

df = pd.DataFrame(linhas)

detalhes_expandido = df['detalhes'].apply(lambda x: x[0] if x else {})
df = pd.concat([df.drop(columns=['detalhes']), detalhes_expandido.apply(pd.Series)], axis=1)

df.to_excel('ocorrencias_jogos.xlsx', index=False)