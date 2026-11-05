# Relatório de testes automatizados — VINT Match

Executado em 05/11/2026 02:03 · Python 3.10.12 · Linux · duração total 24.8 s

**Resultado: 51 de 51 testes passaram. Cobertura de código do pacote `app`: 87%.**

## Por tipo de teste

| Tipo | Testes | Passaram | Tempo (s) |
| --- | --- | --- | --- |
| Ponta a ponta (API) | 1 | 1 | 9.88 |
| Aceite / desempenho | 3 | 3 | 3.34 |
| Componente | 10 | 10 | 1.95 |
| Unitário | 37 | 37 | 0.56 |

## Desempenho do cruzamento das bases

Cenário do José (Node.js + AWS, Sênior, 50%, 3 meses), 20 execuções: mediana **146 ms**, máximo **170 ms**, cruzando 279 colaboradores do SGD e 300 talentos do iHiring.

## Cobertura por módulo

| Módulo | Linhas | Não cobertas | Cobertura |
| --- | --- | --- | --- |
| `app/__init__.py` | 0 | 0 | 100% |
| `app/auth.py` | 77 | 6 | 92% |
| `app/buscas.py` | 319 | 25 | 92% |
| `app/config.py` | 34 | 2 | 94% |
| `app/db.py` | 51 | 17 | 67% |
| `app/extract.py` | 127 | 28 | 78% |
| `app/llm.py` | 300 | 62 | 79% |
| `app/main.py` | 466 | 72 | 85% |
| `app/matching.py` | 246 | 11 | 96% |
| `app/rag.py` | 257 | 42 | 84% |
| `app/sgd.py` | 106 | 0 | 100% |
| `app/store.py` | 35 | 0 | 100% |
| `app/textutil.py` | 36 | 0 | 100% |
| **Total** | 2054 | 265 | **87%** |

## Todos os testes

| Arquivo | Teste | Tipo | Tempo (s) | Resultado |
| --- | --- | --- | --- | --- |
| `test_api.py` | `test_fluxo_completo` | Ponta a ponta (API) | 9.88 | Passou |
| `test_cenario_jose.py` | `test_jose_encontra_quem_atende_e_esta_livre` | Aceite / desempenho | 0.17 | Passou |
| `test_cenario_jose.py` | `test_jose_ve_alternativas_internas_e_externas` | Aceite / desempenho | 0.17 | Passou |
| `test_cenario_jose.py` | `test_desempenho_do_cruzamento_das_bases` | Aceite / desempenho | 3.00 | Passou |
| `test_smoke.py` | `test_somente_leitura` | Componente | 0.08 | Passou |
| `test_smoke.py` | `test_carga` | Componente | 0.00 | Passou |
| `test_smoke.py` | `test_matching` | Componente | 0.43 | Passou |
| `test_smoke.py` | `test_extract_regras` | Componente | 0.01 | Passou |
| `test_smoke.py` | `test_docx` | Componente | 0.09 | Passou |
| `test_smoke.py` | `test_rag` | Componente | 0.72 | Passou |
| `test_smoke.py` | `test_ia_merge_mock` | Componente | 0.62 | Passou |
| `test_smoke.py` | `test_gemini_mock` | Componente | 0.00 | Passou |
| `test_smoke.py` | `test_gemini_diagnostico_mock` | Componente | 0.00 | Passou |
| `test_smoke.py` | `test_reserva_503_para_groq` | Componente | 0.00 | Passou |
| `test_unidades.py` | `test_data_inicio_aceita_datas[2026-12-01-esperado0]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_data_inicio_aceita_datas[01/12/2026-esperado1]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_data_inicio_atalhos_e_texto` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_duracao_entendida[3\u20136 meses-6]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_duracao_entendida[4 meses-4]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_duracao_entendida[10 semanas-3]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_duracao_entendida[1 ano-12]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_duracao_entendida[2 a 4 meses-4]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_duracao_entendida[40 meses-24]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_duracao_entendida[2027-06-30-8]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_duracao_entendida[30/06/2027-8]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_duracao_invalida_e_sinalizada` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_fim_previsto` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_nivel_digitado[Avan\xe7ado-3]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_nivel_digitado[avancado-3]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_nivel_digitado[s\xeanior-3]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_nivel_digitado[especialista-3]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_nivel_digitado[3-3]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_nivel_digitado[Intermedi\xe1rio-2]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_nivel_digitado[pleno-2]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_nivel_digitado[B\xe1sico-1]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_nivel_digitado[-1]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_nivel_digitado[qualquer-1]` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_nome_de_projeto_normalizado_para_duplicidade` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_skill_por_apelido` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_extracao_siglas_e_dedicacao` | Unitário | 0.01 | Passou |
| `test_unidades.py` | `test_filtro_de_senioridade` | Unitário | 0.04 | Passou |
| `test_unidades.py` | `test_proximos_do_ideal_tem_pdi` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_remanejamento_diz_o_que_liberar` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_externos_ordenados_e_limitados` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_mais_dedicacao_exigida_nunca_aumenta_disponiveis` | Unitário | 0.20 | Passou |
| `test_unidades.py` | `test_skill_que_ninguem_tem_vira_lacuna` | Unitário | 0.04 | Passou |
| `test_unidades.py` | `test_alocados_sempre_aparecem` | Unitário | 0.05 | Passou |
| `test_unidades.py` | `test_previa_sem_skills` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_previa_com_skills` | Unitário | 0.05 | Passou |
| `test_unidades.py` | `test_provedor_que_falhou_fica_em_pausa` | Unitário | 0.00 | Passou |
| `test_unidades.py` | `test_ia_falhando_nao_quebra_o_ranking` | Unitário | 0.11 | Passou |

Evidências: `execucao.txt` (saída completa), `junit.xml`, `cobertura/index.html` (linha a linha).
