import json
import pandas as pd
import openpyxl

with open('as.json', 'r', encoding='utf-8') as file:
    dados = json.load(file)

# print(dados[0])

linhas = []

for jogo in dados:
    time_casa = jogo['time_casa']
    time_fora = jogo['time_fora']
    partida = time_casa + ' x ' + time_fora
    _id = jogo['id']
    link = jogo['link']
    placar = jogo['placar']
    rodada = jogo['rodada']
    
    for ocorrencia in jogo['ocorrencia_casa']:
        linha = {
            'id': _id,
            'partida': partida,
            'placar': placar,
            'rodada': rodada,
            'time': time_casa,
            'detalhes': ocorrencia,
            'link': link
        }
        linhas.append(linha)
    
    for ocorrencia in jogo['ocorrencia_fora']:
        linha = {
            'id': _id,
            'partida': partida,
            'placar': placar,
            'rodada': rodada,
            'time': time_casa,
            'detalhes': ocorrencia,
            'link': link
        }
        linhas.append(linha)


df = pd.DataFrame(linhas)

detalhes_expandido = pd.json_normalize(df['detalhes'])
df = pd.concat([df.drop(columns=['detalhes']), detalhes_expandido.apply(pd.Series)], axis=1)

df['data'] = df['id'].apply(lambda x: x.split()[0].replace('.', '/'))

df['rodada'] = df['rodada'].apply(lambda x: x.split('Rodada ')[1])

df['temporada'] = df['data'].apply(lambda x: x.split('/')[2])

df = df[df['ocorrencia']=='wcl-icon-soccer']

df['ocorrencia'] = df['ocorrencia'].replace('wcl-icon-soccer', 'Gol')

df = df[['data', 'partida', 'placar', 'rodada', 'temporada', 'time', 'ocorrencia', 'tempo_ocorrencia']]

df.to_excel('ocorrencias_jogos.xlsx', index=False)