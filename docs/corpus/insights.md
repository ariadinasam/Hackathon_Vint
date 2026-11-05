# Insights de negócio e hipóteses para o hackathon

## O que é esse sistema
O "InHire" é um sistema de **gestão de alocação de profissionais** de uma empresa de serviços de TI (fábrica de software / outsourcing para clientes, provavelmente setor público — há domínios como "Preposto", "Licitações", "Reajuste CCT", "PCCR"). Fluxo: **Contrato → Demandas → Alocações → Planejamento mensal (%)**, com um catálogo de **skills** para casar pessoas internas (colaboradores) ou externas (talentos) com o que cada demanda exige. As funções `ranking_skills`, `buscar_profissionais` e `ranking_talentos` mostram o caso de uso esperado: **"quem está disponível em tal mês e tem as skills X, Y, Z?"**

## Retrato da operação (colaboradores ativos = 231)
- **Senioridade:** Júnior 75 · Sênior 69 · Pleno 60 · Trainee 22 · Master 3 · Especialista 1 · Estagiário 1 → pirâmide "achatada", quase tantos sêniores quanto júniores; topo (Master/Especialista) muito fino.
- **Cargos:** Analista de Sistemas 43, Desenvolvedor 31, Técnico de Suporte 25, Analista de Suporte 19, Técnico de Informática 19, Trainee 17 → ~27% do quadro é suporte/infra técnico.
- **Vínculo × modalidade:** CLT 199 (86%) / PJ 32. Presencial 147 (64%), Híbrido 72, Remoto 12 → operação majoritariamente presencial e CLT.
- **Setor:** praticamente todos no CDS. **Step:** 93% no Step I (plano de carreira pouco usado).
- **Admissões:** crescimento forte a partir de 2023 (59 em 2023, 69 em 2024, 53 em 2025, 41 até out/2026) → ~80% do quadro tem menos de 4 anos de casa.

## Contratos e demandas
- 14 contratos: 6 Ativos, 5 **Vencidos**, 2 A Renovar, 1 Encerrado. Os contratos 5 e 6 (**A Renovar**, vencem em dez/2026) concentram **68 colaboradores distintos alocados** → maior risco comercial de curto prazo.
- Contratos 3 e 4 concentram 58 das 93 demandas ativas; 2 gerentes (ids 267 e 202) cuidam de 64 demandas (69%) → **gargalo de gestão**.
- 93 demandas ativas: Não Iniciada 36 · Concluída 34 · Em Desenvolvimento 13 · Em Atenção 6 · Iniciada 3 · Crítica 1. Tipos: Outsourcing 36, Sustentação 32, Desenvolvimento 19, Apoio 6. Metodologia: Kanban 43 / Scrum 42.
- **Metade das alocações ativas (212 de 424) está em demandas "Não Iniciadas"** → ou o status das demandas está desatualizado, ou há gente reservada sem trabalho efetivo.

## 🔎 As 3 descobertas mais interessantes
1. **"Penhasco" de capacidade nos próximos meses.** Disponibilidade dos 231 ativos (mesma regra de `disponibilidade_mensal`):

   | Mês | 100% livres | FTE livre |
   |---|---:|---:|
   | Out/26 | 65 | 66,6 |
   | Nov/26 | 131 | 132,5 |
   | Dez/26 | 172 | 174,8 |
   | Jan/27 | 217 | 217,0 |
   | Fev/27 | 228 | 228,0 |

   A média de % planejado cai de ~99% (dez/25) para 19% (dez/26). Ou o horizonte de planejamento é curto (não registram o futuro), ou há **ociosidade/bench iminente** coincidindo com o vencimento dos contratos 5 e 6. É o problema de negócio mais "vendável" para o hackathon.
2. **O cadastro de skills não discrimina ninguém.** Média de 62 skills por pessoa; 57 colaboradores marcaram praticamente todo o catálogo (121–129 skills) e 56% dos registros são BÁSICO. Ao mesmo tempo, 57 ativos não têm nenhuma skill. Todas as 49 skills demandadas têm entre 4 e 48 colaboradores "avançados" no papel → um ranking por contagem de skills (como `ranking_skills`) devolve muita gente empatada. **Oportunidade:** pontuar por nível (AVANCADO > INTERMEDIARIO > BASICO), pela experiência real (alocações passadas em demandas que exigiam a skill) e penalizar perfis "marquei tudo".
3. **Demanda concentrada em um stack PHP/JS + bancos relacionais.** Top skills exigidas: Laravel/PHP (26 demandas cada), JavaScript (24), Vue.js (20), TypeScript (19), Oracle (18), Trello (17), PostgreSQL (16). Já o catálogo recém-ampliado (Rust, Go, C#, Terraform, Ansible, área "Desenvolvimento legado" — COBOL, Delphi, ABAP…) tem **zero** colaboradores → ou é aposta futura, ou é demanda não atendível internamente (aqui entram os `talentos` externos).

## Outros sinais
- 13 colaborador-mês com **200% de alocação** (ex.: colaboradores 63 e 140 em jul–set/26) e 20 alocações ativas presas a demandas já concluídas.
- 34 demandas com término previsto no passado e não concluídas; 49 demandas fora da vigência do contrato.
- Talentos externos: base **sintética** (distribuição uniforme, 5 skills cada) — ótima para demonstrar o matching, inútil para estatística.

## 💡 Perguntas / hipóteses para o hackathon
**Alocação e capacidade**
1. Quem estará ocioso (bench) em cada um dos próximos 3 meses e quais skills essas pessoas têm? → "Painel de bench".
2. O penhasco de capacidade é real ou é falta de planejamento? Compare % planejado por contrato com o fim de vigência.
3. Quais colaboradores estão sobrealocados (>100%) e quais demandas poderiam absorver redistribuição?
4. Quanto de capacidade está presa em demandas Concluídas / Não Iniciadas?

**Matching de skills (núcleo do produto)**
5. Para uma demanda nova (lista de skills + mês + senioridade), quem é o melhor candidato interno disponível e, se não houver, qual talento externo cobre? (Combinar `ranking_skills` + `ranking_talentos`.)
6. Um score melhor: peso por nível, por obrigatoriedade (domínio NIVEL_IMPORTANCIA existe mas não é usado em `demanda_skills`), por histórico de alocação e penalidade a perfis inflados.
7. Quais skills são gargalo (alta demanda × poucos AVANÇADOS livres no mês)? → recomendação de treinamento ou contratação.
8. Normalizar o catálogo (Postgre/PostgreSQL, PHP/Laravel, skills duplicadas entre áreas) e medir o ganho de precisão do matching.

**Gestão e risco**
9. Risco de renovação: colaboradores e receita (proxy: FTE) expostos a contratos A Renovar/Vencidos.
10. Carga por gerente (2 gerentes com 69% das demandas) e alerta de demandas atrasadas.
11. "Data quality score" automático usando `vw_inconsistencias_dominios` + as checagens deste relatório.

**Ideias de produto (MVP de 24–48h)**
- *Alocador inteligente*: input = demanda (skills, período, % necessário); output = top-N internos com disponibilidade + top-N talentos externos + gaps.
- *Radar de bench*: timeline mensal de disponibilidade por pessoa/skill, com alerta de contratos vencendo.
- *Auditor de cadastro*: lista acionável de inconsistências (sobrealocação, alocação em demanda concluída, skills infladas).
