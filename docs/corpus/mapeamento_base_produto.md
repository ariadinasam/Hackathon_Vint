# Mapeamento base → produto (VINT Match)

Fonte: schema `"InHire"` (ver `_extraido/relatorio/schema.md`). Legenda: ✅ existe · 🟡 derivado · 🔴 não existe → tratamento.

## Dados do colaborador (SGD)
| Campo do produto | Origem | Status | Observação / tratamento |
|---|---|---|---|
| Nome | `colaboradores.nome_abreviado` | ✅ | PII (fictício "Mocado"); exibir na UI, nunca em log. Logs usam `id`. |
| Cargo / senioridade / vínculo / modalidade | `colaboradores.id_cargo/id_senioridade/id_vinculo/id_modalidade` → `dominios.valor_dominio` | ✅ | 1 registro com senioridade apontando p/ CARGO (id 3) → exibir "não informado". |
| Ativo | `colaboradores.status AND NOT deletado` | ✅ | |
| Skills + nível | `colaborador_skills` (+`skills`, `dominios` AREA_TECNOLOGIA/NIVEL) | ✅ | 57 ativos sem skill; 57 com ~catálogo todo → penalidade de "perfil inflado". Aliases: Postgre≈PostgreSQL, PHP≈Laravel(PHP). |
| Projetos alocados (atuais) | `alocacoes` (ativas) → `demandas` → `contratos` | ✅ | Usar contrato via demanda (não `colaboradores.id_contrato`, incoerente). |
| Disponibilidade no período | `planejamentos` × `alocacoes` ativas = 100 − Σ% por mês | 🟡 | Mesma regra da função `disponibilidade_mensal`; ignorar planejamentos de alocações deletadas. Mês é texto → converter. |
| Tempo gasto no projeto atual | `planejamentos` (meses com % > 0 até o mês corrente) | 🟡 | Derivado: nº de meses e FTE-mês acumulado na demanda. Não há horas apontadas. |
| Duração do projeto | `demandas.dt_inicio_demanda` / `dt_termino_demanda_prevista` | ✅ | 17 demandas com início = fim (placeholder) → marcar "datas não confiáveis". |
| Status do projeto | `demandas.id_andamento_demanda` → dominios | ✅ | Base para a flag de remanejamento (Concluída/Não Iniciada = fácil de liberar). |
| Líder a acionar | `demandas.id_gerente` → colaboradores | ✅ | Usado no card de remanejamento ("falar com gerente X"). |
| Histórico de projetos | todas as `alocacoes` (inclusive deletadas = encerradas) + `planejamentos` passados | 🟡 | 223 ativos têm alguma alocação; só **83** em demandas com skills cadastradas. |
| "Projeto parecido" | `demanda_skills` + `tipo_servico` + `metodologia` das demandas do histórico | 🟡 | 🔴 **Não há descrição textual de projetos** (`nome_demanda` = "Demanda N"). Similaridade = skills + tipo de serviço + metodologia. Opcional: perfil textual gerado a partir desses atributos (determinístico, não inventado). |

## Base de talentos (iHiring)
| Campo | Origem | Status | Tratamento |
|---|---|---|---|
| Talentos externos | `talentos` + `talento_skills` | ✅ ⚠️ | Existe, e o próprio schema se chama **InHire** (a Vint usa o ATS InHire: vintglobal.inhire.app) → "iHiring" ≈ **InHire**. Porém os dados são **sintéticos** (uniformes, 5 skills cada, mesma data). Exibir badge "InHire · dado de teste". |
| Disponibilidade informada | `talentos.disponibilidade_informada_percentual` | ✅ | Valor declarado, sem calendário mensal. |

## Entrada do usuário
| Campo | Uso | Status |
|---|---|---|
| Skills necessárias | casam com `skills.nome_skill` (normalizado + aliases); marcação Obrigatória/Desejável | ✅ / 🟡 (domínio NIVEL_IMPORTANCIA existe, mas `demanda_skills` não tem a coluna → o usuário marca no formulário) |
| Duração / período | meses consultados em `planejamentos` | ✅ |
| Disponibilidade requerida (%) | limiar por mês | ✅ |
| Texto livre | extração de skills/senioridade + similaridade semântica | 🟡 |
| Upload PDF/DOCX | extração de texto (pypdf/python-docx) → requisitos | 🟡 |

## Saídas
| Saída | Origem | Status |
|---|---|---|
| Score + justificativa | cálculo híbrido + texto (LLM ou template) | 🟡 |
| Disponibilidade no período | planejamentos | ✅ |
| Flag de remanejamento | alocações ativas no período + status da demanda + gerente | 🟡 |
| PDI | gap = skills exigidas ausentes ou abaixo do nível; skills "vizinhas" da mesma área | 🟡 · 🔴 **não há catálogo de cursos** (domínios STATUS_CURSO/LNC existem, mas sem tabela) → PDI sugere trilha por skill/área, sem curso real |
| RAG | 🔴 **não há documentação no banco** → corpus = README, relatórios em `_extraido/relatorio`, anotações do cliente (`docs/`) + fichas de skills/demandas geradas dos dados | 🟡 |
