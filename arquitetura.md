# Arquitetura — VINT Match

## Visão geral
```
 Usuário (navegador)
   │  formulário / upload de briefing / pergunta
   ▼
 SPA (app/static: index.html + spa.js + vint.css do design Vint_Global; JS puro, rotas por hash)
   │  JSON
   ▼
 API FastAPI (app/main.py)
   ├── /api/extract  → extract.py  : PDF/DOCX/TXT → texto → requisitos (IA ou regras)
   ├── /api/match    → matching.py : filtro determinístico + score + histórico + remanejamento + PDI
   │                   └── llm.py  : Gemini ou Claude reavalia top-8 (aderência + justificativa + PDI), nomes pseudonimizados
   ├── /api/rag      → rag.py      : TF-IDF sobre docs/corpus + fichas do SGD → IA responde citando [n]
   └── /api/meta     → catálogo de skills, domínios, status da fonte e da IA

 Cursor (chat Agent) ──MCP stdio──► mcp_server.py → mesmas funções (matching, sgd, rag); o LLM é o do Cursor
   │
   ▼
 sgd.py (modelo em memória, carregado 1x na subida, ~20 mil linhas)
   ▼
 db.py  ── Postgres "InHire" (docker do hackathon, sessão default_transaction_read_only=on)
        └─ fallback: data/sgd_snapshot.sqlite (mode=ro&immutable=1)
```

## Banco do app × SGD
```
 SGD (Postgres "InHire" ou snapshot SQLite) ──somente leitura──► sgd.py (memória)
 data/app.db (SQLite do app) ◄──escrita──► store.py: usuarios · sessoes · buscas (params + resultado) · decisoes
```
Autenticação: PBKDF2-SHA256, cookie httpOnly/SameSite=Lax, convite/redefinição por token de uso único (48 h),
bloqueio após 5 erros (15 min ou desbloqueio pelo Admin), perfis Admin/Usuário verificados na API.

## Decisões
| Tema | Decisão | Por quê |
|---|---|---|
| Stack | Python 3.10+ / FastAPI + front sem build | Roda com `pip install` + `uvicorn`; fácil de editar no Cursor (regras em `.cursor/rules`). |
| Dados | Carga completa em memória | Base pequena; cálculo de disponibilidade em ~100 ms; zero escrita no banco. |
| Somente leitura | Sessão Postgres read-only + SQLite `immutable` + teste que bloqueia DML/DDL no código | Guardrail do desafio. |
| Matching | Híbrido: regras explicáveis + IA só no top-8 | Decisão em segundos e auditável; IA dá contexto sem virar caixa-preta. |
| Semântica | TF-IDF local (sempre) + julgamento da IA (opcional) | Funciona offline; a IA cobre a nuance do texto livre. Embeddings do Gemini são um próximo passo natural. |
| LLM | Gemini (`GEMINI_MODEL`, padrão `gemini-3.8-flash`) ou Claude, escolhido por `LLM_PROVIDER` | Usa a chave que a equipe tiver; Gemini via REST, sem dependência extra. |
| Cursor | Servidor MCP (`mcp_server.py` + `.cursor/mcp.json`) | Quem já trabalha no Cursor consulta o matchmaking pelo chat; o modelo do Cursor raciocina e o MCP entrega os dados (nomes pseudonimizados). |
| LGPD | Nomes nunca vão para a IA nem para logs; acesso só com login | Dados pessoais tratados como sensíveis. |
| Resiliência | Sem chave ou com erro de API → tudo funciona por regras | A demo não depende de rede. |

## Score
```
score = 40% skills      (crédito por nível: atende=1, 1 nível abaixo=0,6, 2 abaixo=0,35; obrigatória pesa 2×)
      + 25% disponib.   (média mensal de min(livre/necessário, 1) no período)
      + 20% histórico   (máx. sobre demandas já trabalhadas: 70% skills em comum + 20% mesmo tipo de serviço + 10% mesma metodologia)
      + 15% aderência   (TF-IDF texto livre × perfil; com IA ativa = nota 0–100 da IA)
      − 8 pontos se o perfil declara ≥ 100 skills (dado pouco confiável)
```
- **Filtro determinístico:** colaboradores ativos, senioridade (se informada) e todas as skills obrigatórias. Uma skill obrigatória que ninguém tem vira lacuna (não bloqueia o ranking).
- **Remanejamento:** quem não tem a disponibilidade mínima em algum mês recebe o selo; se a aderência técnica for ≥ a do melhor disponível, recebe "Mais viável" e entra no ranking mesmo fora do top-10. O card mostra quanto liberar por mês, quais demandas ocupam a pessoa, status, contrato, gerente e uma sugestão (demanda concluída/não iniciada = fácil).
- **PDI:** para cada skill ausente ou abaixo do nível: prazo estimado, skills da mesma área que a pessoa já domina, mentor interno (colega avançado com mais disponibilidade) e demanda ativa onde praticar. Não há catálogo de cursos no SGD.
- **Disponibilidade:** mesma regra da função `"InHire".disponibilidade_mensal` (100 − Σ% das alocações ativas no mês). Planejamentos de alocações deletadas são ignorados.

## Limitações conhecidas (dados)
- Não há descrição textual das demandas ("Demanda N"): "projeto parecido" usa skills, tipo de serviço e metodologia.
- Planejamento registrado só até fev/2027; meses seguintes aparecem 100% livres (aviso na tela).
- Talentos InHire são sintéticos (marcados na UI).
- Ver `docs/mapeamento_base_produto.md` e `docs/corpus/qualidade_dados.md`.

## Próximos passos
Embeddings reais (ex.: modelo local) para RAG maior; escrita de "reservas" num schema próprio (fora do SGD); integração real com a API do InHire; autenticação e trilha de auditoria.
