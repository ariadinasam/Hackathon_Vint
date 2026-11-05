# Relatório de qualidade dos dados — schema "InHire"

Data de referência da análise: 2026-11-03. Regras de "ativo": `status = true AND deletado = false`.
Consultas correspondentes em `queries.sql` (seção 3).

## 🔐 Dados pessoais (LGPD)
- `colaboradores.nome_abreviado` (279) e `talentos.nome_abreviado` (300) são **nomes de pessoas**. Todos os colaboradores têm o sufixo "Mocado" e as funções chamam a coluna de `nome_ficticio`, o que indica dados **fictícios/anonimizados** — ainda assim trate como sensível: não exponha em demos públicas, não envie para APIs externas e não inclua em prints.
- Não foram encontrados CPF, e-mail, telefone ou endereço nas tabelas. `data_admissao` + cargo + nome pode ser quase-identificador.
- O arquivo `.env` contém a senha do banco (token pessoal). **Não foi lido** nesta análise; não versione nem compartilhe.

## Resumo por severidade

| # | Severidade | Problema | Qtde | Impacto |
|---|---|---|---:|---|
| 1 | 🔴 Alta | `planejamentos` ativos ligados a `alocacoes` deletadas (soft delete não propagou) | 1.290 de 4.744 (27%) | Qualquer soma de % que não faça JOIN filtrando `alocacoes.deletado` fica inflada |
| 2 | 🔴 Alta | Sobrealocação (>100% num mês, considerando só alocações ativas) | 13 colaborador-mês (até 200%) | Disponibilidade negativa em `disponibilidade_mensal` |
| 3 | 🔴 Alta | Alocações ativas de colaboradores inativos/deletados | 57 | Contam no total alocado; colaborador some das buscas |
| 4 | 🟠 Média | Colaborador com `id_senioridade` apontando para um **CARGO** (id 139 "Trainee") — colaborador id 3 | 1 | Exatamente o que `vw_inconsistencias_dominios` detecta; quebra joins por senioridade |
| 5 | 🟠 Média | Demandas fora da vigência do contrato (início antes / término depois) | 49 de 95 | Regra de negócio não validada no banco |
| 6 | 🟠 Média | Demandas com término previsto já passado e não concluídas | 34 | "Atrasadas" de fato, mas `andamento` não reflete |
| 7 | 🟠 Média | Demandas com `dt_inicio = dt_termino_prevista` (17 delas em 2026-05-25) | 17 | Datas-placeholder de carga |
| 8 | 🟠 Média | Alocações ativas em demandas **Concluídas** com planejamento > 0 após nov/2026 | 20 | Capacidade presa em projeto encerrado |
| 9 | 🟠 Média | `colaboradores.id_contrato` incoerente com contratos das alocações (ex.: Contrato 14 tem 21 colaboradores e 0 demandas; Contrato 9 tem 38 alocados e 0 vinculados) | — | Use alocações→demandas→contratos, não `colaboradores.id_contrato` |
| 10 | 🟠 Média | Contratos **Vencidos** com 48 colaboradores ativos vinculados (Contrato 8) e alocações ativas em nov/2026 (Contratos 2, 3, 8) | 3 contratos | Risco comercial / cadastro desatualizado |
| 11 | 🟡 Baixa | Skills com mesmo nome em áreas diferentes (Docker, Kubernetes, BPMN, UML, Vault, Nginx…) | 11 nomes | `ranking_skills` faz match por nome → ambíguo |
| 12 | 🟡 Baixa | Quase-duplicatas no catálogo: `Postgre` × `PostgreSQL`, `PHP` × `Laravel (PHP)`, `Flutter` × `Flutter Test` | ≥2 pares | Fragmenta oferta/demanda de skills |
| 13 | 🟡 Baixa | Skills sem nenhum colaborador (toda a área "Desenvolvimento legado" + Rust, Go, C#, Terraform, Ansible…) | 26 de 159 | Catálogo novo não preenchido |
| 14 | 🟡 Baixa | Colaboradores ativos sem nenhuma skill | 57 de 231 | Invisíveis para matching |
| 15 | 🟡 Baixa | Inflação de skills autodeclaradas: média 62 skills/colaborador; **57 pessoas marcaram ≥121 das 129 skills preenchíveis**; 56% dos registros em nível BÁSICO | 57 | Score por contagem de skills fica enviesado |
| 16 | 🟡 Baixa | `planejamentos.porcentagem = 0` | 1.370 (29%) | Linhas-placeholder; filtrar `> 0` para contar alocações reais |
| 17 | 🟡 Baixa | `planejamentos.mes` é texto (`Jan..Dez`) | — | Ordenar/filtrar por período exige conversão |
| 18 | 🟡 Baixa | Nomes duplicados em colaboradores (ids 35/246, 152/153, 169/327) | 3 pares | Possível cadastro duplicado da mesma pessoa |
| 19 | 🟡 Baixa | Gerente de demanda e preposto de contrato inativos | 1 + 1 | Responsável inexistente |
| 20 | ℹ️ Info | `talentos` é **sintético**: todos com `criado_em` idêntico, todos Remoto, exatamente 5 skills cada, distribuição perfeitamente uniforme de senioridade (37–38) e disponibilidade (0–100 de 10 em 10, ~26 cada), 15 sobrenomes | 300 | Não tire conclusões estatísticas de talentos; serve para demo de matching |

## Nulos relevantes
| Tabela.coluna | Nulos | % |
|---|---:|---:|
| demandas.id_grupo | 80 | 84,2% |
| colaboradores.id_contrato | 105 | 37,6% |
| colaboradores.data_admissao | 5 | 1,8% |
| colaboradores.id_setor_empresa | 4 | 1,4% |
Demais colunas: 0 nulos (ver `estatisticas.csv`).

## Duplicatas
- Nenhuma duplicata ativa em (colaborador, skill), (demanda, skill) ou (colaborador, demanda). Existem 3 pares (colab, skill) e 19 pares (colab, demanda) duplicados quando se incluem registros deletados — histórico de soft delete, OK.
- Nenhum nome de contrato, demanda ou talento duplicado.

## Integridade referencial
- Todas as FKs estão íntegras (o dump as cria com constraint). O único problema de tipo de domínio é o item 4.
- Lacunas de ids (sequences maiores que contagens: alocacoes 635 vs 617, colaboradores 336 vs 279, planejamentos 5.039 vs 4.744) indicam **exclusões físicas** anteriores ao dump.
- `dominios`: 67 dos 88 CENTRO_CUSTO estão deletados (nenhum é referenciado). Muitos tipos de domínio (MOTIVO_AUSENCIA, SITUACAO_FERIAS, STATUS_PAGAMENTO, TIPO_DEMANDA…) não são usados por nenhuma tabela deste recorte — vêm de um sistema maior.

## Outliers óbvios
- `planejamentos`: soma mensal por colaborador chega a 200% (item 2).
- `colaborador_skills`: 57 colaboradores com 121–129 skills (praticamente todo o catálogo preenchível) — provável preenchimento em massa / "marcar tudo".
- `demandas`: duração de 0 dias (item 7); maior término previsto 2028-12-31.
- `colaboradores.id_step`: 92% no Step I — pouca variação, baixo valor analítico.
