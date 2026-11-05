# Mapa do schema — banco `hackathon`, schema `"InHire"`

**Tecnologia:** PostgreSQL (dump `pg_dump` em SQL texto; origem PG 17.9, pg_dump 18.4, gerado em 2026-10-27). O ambiente oficial sobe via Docker (`postgres:18-alpine`).
**Arquivo:** `db/01-hackathon.sql` — 621 KB, 21.795 linhas. Não havia zip: a pasta já veio descompactada. Cópia de trabalho em `_extraido/fonte/` (SHA-256 idêntico ao original).
**Conteúdo:** 11 tabelas, 1 view, 5 funções PL/pgSQL, 33 FKs, 37 índices, **20.068 linhas** no total.

> Como não há Postgres/Docker no ambiente de análise, os dados das seções `COPY` foram convertidos (somente leitura) para `_extraido/hackathon.sqlite` pelo script `_extraido/scripts/carregar_sqlite.py`. Nenhum comando do dump foi executado.

## Tabelas

| Tabela | Linhas | Papel |
|---|---:|---|
| `dominios` | 320 | Tabela genérica de listas de valores (33 `tipo_dominio`: CARGO, SENIORIDADE, CENTRO_CUSTO…) |
| `colaboradores` | 279 | Profissionais internos |
| `colaborador_skills` | 11.727 | Skills × colaborador com nível (BASICO/INTERMEDIARIO/AVANCADO) |
| `skills` | 159 | Catálogo de skills por área de tecnologia |
| `contratos` | 14 | Contratos com clientes |
| `demandas` | 95 | Projetos/demandas de um contrato |
| `demanda_skills` | 313 | Skills exigidas por demanda |
| `alocacoes` | 617 | Vínculo colaborador × demanda |
| `planejamentos` | 4.744 | % de alocação mensal por alocação (mês texto `Jan..Dez` + ano) |
| `talentos` | 300 | Candidatos externos |
| `talento_skills` | 1.500 | Skills dos talentos (exatamente 5 por talento) |

### Colunas e tipos
Padrão em quase todas as tabelas: `id bigint PK` (sequence) + `status boolean DEFAULT true` + `deletado boolean DEFAULT false` (soft delete).

- **dominios**: id, tipo_dominio varchar(100) NN, valor_dominio varchar(100) NN, descricao varchar(255), status, deletado
- **colaboradores**: id, nome_abreviado varchar(255) NN ⚠️PII, data_admissao timestamptz, id_cargo→dominios NN, id_senioridade→dominios NN, id_step→dominios NN, id_vinculo→dominios NN, id_modalidade→dominios NN, id_setor_empresa→dominios, id_contrato→contratos (DEFERRABLE), status, deletado
- **colaborador_skills**: id, id_colaborador→colaboradores, id_skill→skills, nivel_conhecimento varchar(20) CHECK (BASICO/INTERMEDIARIO/AVANCADO), id_nivel_conhecimento→dominios, status, deletado
- **skills**: id, nome_skill varchar(100), id_area_tecnologia→dominios, status, deletado — UNIQUE (id_area_tecnologia, lower(trim(nome_skill)))
- **contratos**: id, nome_contrato varchar(100), data_inicio date, data_termino date (CHECK termino ≥ inicio), id_situacao→dominios, id_centro_custo→dominios, id_preposto→colaboradores (DEFERRABLE), status, deletado
- **demandas**: id, nome_demanda varchar(100), id_gerente→colaboradores, id_contrato→contratos, id_tipo_servico→dominios, id_metodologia→dominios, id_andamento_demanda→dominios, id_grupo→dominios, dt_inicio_demanda date, dt_termino_demanda_prevista date (CHECK ≥ início), compartilha_profissionais bool, pertence_pmo bool, status, deletado
- **demanda_skills**: id, id_demanda→demandas, id_skill→skills, status, deletado
- **alocacoes**: id, id_colaborador→colaboradores, id_demanda→demandas, status, deletado
- **planejamentos**: id, id_alocacao→alocacoes, mes varchar(3) CHECK (Jan..Dez), ano int, porcentagem int CHECK 0–100, status, deletado — UNIQUE (id_alocacao, mes, ano)
- **talentos**: id, nome_abreviado varchar(255) ⚠️PII, id_cargo/id_senioridade/id_modalidade→dominios, disponibilidade_informada_percentual int CHECK 0–100, status, criado_em timestamptz
- **talento_skills**: id, id_talento→talentos (ON DELETE CASCADE), id_skill→skills, id_nivel_conhecimento→dominios — UNIQUE (id_talento, id_skill)

## Diagrama de relacionamentos (ASCII)

```
                 id_preposto (N:1)
   contratos ─────────────────────────────► colaboradores ◄──────────── id_gerente (N:1) ─────┐
     │    ▲                                  │   │    │                                      │
     │    └──── id_contrato (N:1, opcional) ─┘   │    │ 1:N                                  │
     │ 1:N                                       │    ▼                                      │
     ▼                                           │  colaborador_skills ──N:1──► skills ◄─┐   │
   demandas ◄───────────────────────────────────┼──────────────────────────────────────┼───┘
     │   │ 1:N                                  │ 1:N                                  │
     │   ▼                                      ▼                                      │
     │  demanda_skills ──N:1──► skills       alocacoes (colaborador × demanda)         │
     │                                          │ 1:N                                  │
     └──────────── 1:N ───────────────────────► │                                      │
                                                ▼                                      │
                                           planejamentos (mês/ano/%)                   │
                                                                                       │
   talentos ──1:N──► talento_skills ──N:1──────────────────────────────────────────────┘

   dominios ◄── todas as colunas id_cargo, id_senioridade, id_step, id_vinculo, id_modalidade,
                id_setor_empresa, id_situacao, id_centro_custo, id_tipo_servico, id_metodologia,
                id_andamento_demanda, id_grupo, id_area_tecnologia, id_nivel_conhecimento
```

Leitura simplificada:
```
contratos 1─N demandas 1─N alocacoes N─1 colaboradores
                                 1─N planejamentos (mês a mês, %)
demandas  N─N skills   (via demanda_skills)
colaboradores N─N skills (via colaborador_skills, com nível)
talentos  N─N skills   (via talento_skills, com nível)
colaboradores 1─N demandas (como gerente) · colaboradores 1─N contratos (como preposto)
colaboradores N─1 contratos (id_contrato, opcional)
```

## Lista de FKs (33)
| Origem | → Destino | Regra |
|---|---|---|
| alocacoes.id_colaborador | colaboradores.id | RESTRICT |
| alocacoes.id_demanda | demandas.id | RESTRICT |
| planejamentos.id_alocacao | alocacoes.id | RESTRICT |
| colaborador_skills.id_colaborador | colaboradores.id | RESTRICT |
| colaborador_skills.id_skill | skills.id | RESTRICT |
| colaborador_skills.id_nivel_conhecimento | dominios.id | RESTRICT |
| colaboradores.id_cargo / id_senioridade / id_step / id_vinculo / id_modalidade / id_setor_empresa | dominios.id | RESTRICT (6 FKs) |
| colaboradores.id_contrato | contratos.id | DEFERRABLE |
| contratos.id_situacao / id_centro_custo | dominios.id | RESTRICT (2) |
| contratos.id_preposto | colaboradores.id | DEFERRABLE (ciclo com colaboradores.id_contrato) |
| demandas.id_contrato | contratos.id | RESTRICT |
| demandas.id_gerente | colaboradores.id | RESTRICT |
| demandas.id_tipo_servico / id_metodologia / id_andamento_demanda / id_grupo | dominios.id | RESTRICT (4) |
| demanda_skills.id_demanda / id_skill | demandas.id / skills.id | RESTRICT (2) |
| skills.id_area_tecnologia | dominios.id | RESTRICT |
| talentos.id_cargo / id_senioridade / id_modalidade | dominios.id | RESTRICT (3) |
| talento_skills.id_talento | talentos.id | **CASCADE** |
| talento_skills.id_skill / id_nivel_conhecimento | skills.id / dominios.id | RESTRICT (2) |

⚠️ As FKs para `dominios` **não garantem o tipo** (ex.: `id_senioridade` pode apontar para um CARGO). Por isso existe a view `vw_inconsistencias_dominios`.

## View e funções (lógica de negócio pronta)
| Objeto | Assinatura | O que faz |
|---|---|---|
| `vw_inconsistencias_dominios` | view | Lista FKs para `dominios` cujo `tipo_dominio` não bate com o esperado |
| `disponibilidade_mensal(ano, mes)` | → id_colaborador, total_alocado, disponibilidade (=100−Σ%) | Soma `planejamentos` de alocações ativas no mês; inclui todos os colaboradores (LEFT JOIN) |
| `disponibilidade_periodo(ano_ini, mes_ini, ano_fim, mes_fim)` | → média/mín/máx disponibilidade, meses sem alocação | Até 61 meses |
| `buscar_profissionais(ano, mes, senioridade, skills[], disp_min, cargos[], colaborador)` | → colaboradores ativos | Filtro com match **completo** por id de skill |
| `ranking_skills(ano, mes, skills text[], disp_min, match_completo, senioridade)` | → score % de aderência | Match por **nome** de skill (lower/trim) + disponibilidade |
| `ranking_talentos(skills text[], match_completo)` | → score % de talentos externos | Mesmo match por nome |

Exemplo (no Postgres): `SELECT * FROM "InHire".ranking_skills(2026, 12, ARRAY['PHP','Vue.js','PostgreSQL'], 50);`
