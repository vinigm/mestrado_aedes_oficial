# Novas fontes oficiais de dados — levantamento de 25/09/2026

**Pedido do Vinicius:** *"vc tá liberado pra tentar conseguir mais dados tanto de casos de dengue quanto
outros desde que sejam fontes oficiais"*. Quatro frentes em paralelo, cada uma com verificador
independente que refez as consultas do zero. **Nada foi integrado ao pipeline.**

## O que foi obtido

| Arquivo | Fonte oficial | Conteúdo | Verificado |
|---|---|---|---|
| `dados/cevs_poa_dengue_semanal_por_medida.csv` | SES-RS / CEVS, API ArcGIS | dengue POA, semanal, 2015-2026, 7 medidas, por **residência** | ✅ 2022 = 5.142 e 2025 = 22.504 batem com a medição de 13/09 |
| `dados/cevs_poa_chikungunya_semanal_por_medida.csv` | SES-RS / CEVS | chikungunya POA 2015-2026 | ✅ 57 confirmados no total |
| `dados/cevs_poa_zika_semanal_por_medida.csv` | SES-RS / CEVS | zika POA 2015-2026 | ✅ 35 confirmados no total |
| `dados/cevs_regiao_metropolitana_dengue_confirmados_semanal.csv` | SES-RS / CEVS | dengue confirmada de 11 municípios vizinhos, 2015-2026 | ✅ |
| `dados/tabnet_dengue_poa_residencia_2014-2017_semana_epidem_notif.csv` | DATASUS / TabNet | casos prováveis POA 2014-2017, por residência | ✅ 453 no total |
| `dados/ibge_populacao_poa.csv` | IBGE / SIDRA 6579 | população de POA; faltam 2022 e 2023 | ✅ |
| `dados/datasus_ftp_sinan_dengue_chik_zika_inventario.csv` | DATASUS / FTP | inventário de DENGBR13-17, CHIKBR, ZIKABR com tamanho | ✅ |
| `dados/sinan_arboviroses_prefeitura_poa_2010_2022.csv` | SMS-POA / dadosabertos.poa.br | 12.038 notificações, 2010-2022, sem confirmação | ✅ ⚠️ **não commitado**: registro por pessoa |

Acesso ao CEVS: usar `curl`. O `urllib` do Python falha na cadeia de certificado do servidor.

## O que não foi obtido, e por quê

- **INMET, estação oficial de POA (A801).** A API pública de série histórica devolve vazio; a com token
  exige cadastro no BDMEP. Os pacotes anuais nacionais têm 60 a 115 MB cada. Não baixados.
- **DENGBR13 a DENGBR17** do FTP do DATASUS: 10 a 72 MB cada, em `.dbc`, que exige a biblioteca `pysus`.
  Não baixados.
- **Dados "vintage"**, a contagem como estava em cada semana antes de amadurecer: não existem como dado.
  A SES-RS só publica boletins em PDF, e a API do InfoDengue não guarda versões antigas.

## Dois achados que mudam o plano

**1. 2015 a 2017 não foram anos de epidemia em POA.** Confirmados pelo CEVS: 75, 356 e 2. A série inteira
tem **quatro temporadas epidêmicas, todas de 2022 em diante**. Estender a série para trás acrescenta
semanas calmas, não exemplos de epidemia.

**2. Em 2022 e 2023 os vizinhos NÃO sobem antes de POA.** Semana em que a subida começa, 20% do pico da
temporada, média móvel de 3 semanas. Positivo = o vizinho sobe antes de POA.

| Temporada | Faixa entre os 11 vizinhos | Região somada |
|---|---|---|
| 2022 | −4 a −1 semanas | −1 |
| 2023 | −3 a +4 semanas | 0 |

Em 2022 todos os vizinhos sobem **depois**. Descritivo, duas temporadas, e medido **só em 2022-2023** para
não olhar de novo o período de avaliação 2024-2025. A hipótese de que a dengue chega a POA pela região
metropolitana não se sustenta nesses dados.

## Ressalva de definição

O CEVS e o TabNet contam por **município de residência**. O alvo atual do modelo conta por **município de
notificação**, ~10% acima em POA, que é polo regional. Usar qualquer destes dados junto do alvo atual exige
decidir antes qual definição o projeto adota — pendente desde 13/09/2026.
