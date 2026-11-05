# Roteiro de demo — 3 minutos

**Preparação (antes de subir no palco)**
- `run.bat` rodando, navegador em http://localhost:8000, zoom 90%.
- `.env` com `GEMINI_API_KEY` **e** `GROQ_API_KEY` (reserva automática se o Gemini estiver sobrecarregado). Faça uma busca de aquecimento e confira "Ranking refinado por IA". Sem internet? Desmarque "Refinar com IA": tudo funciona por regras.
- Crie o Admin no primeiro acesso e faça uma busca de aquecimento.
- Deixe aberto o Explorer em `docs/exemplos/`.

---

**0:00–0:30 · A dor**
> "Hoje, quando chega um projeto, alguém abre o SGD, lista quem tem as skills e clica um a um para ver a disponibilidade dos
> próximos 3 meses. Quando não acha, começa a rodada de ligações para os líderes."

**0:30–1:10 · Entrada sem digitar dados de colaborador**
1. Já logado, no **Início**, mostre os indicadores e clique **Iniciar busca**.
2. Arraste `docs/exemplos/briefing_portal_servicos_EXEMPLO.docx` para o card **Briefing**: nome, descrição, skills
   (obrigatórias/desejáveis), duração, início, dedicação, senioridade e metodologia se preenchem sozinhos.
> "A IA leu o briefing e traduziu para o vocabulário do SGD. Eu só reviso."

**1:10–2:10 · O resultado**
3. **Gerar matchmaking** → skeleton → ranking em segundos. Mostre internos × iHiring, o alerta âmbar
   (“mais viável está alocado”), o toggle **Considerar remanejamento** e o filtro.
4. Abra **Ver detalhes** de quem tem remanejamento: *Por que este match*, a linha do tempo (barra tracejada = proposta),
   **Remanejamento sugerido** (o que liberar, com quem falar e quem cobre a saída) e o **PDI**.
5. Volte, **Selecionar** 2–3 talentos → barra inferior → **Confirmar seleção**. Mostre que dá para ajustar a % de cada um, **Adicionar ao projeto** mais alguém de *Também sugeridos* e **Editar projeto** (as pessoas alocadas continuam). A busca passa a mostrar **Selecionados para o projeto** no topo e **Também sugeridos** abaixo; no **Início**, a decisão aparece em *Últimas decisões*.
   Clique **Relatório**: pessoas alocadas, motivos, skills, disponibilidade mês a mês, cobertura e pontos de atenção. Marque o que entra e use **Imprimir / salvar PDF**, **Baixar planilha (CSV)** ou **Copiar resumo**.

**2:10–2:40 · Governança**
6. Menu do usuário → **Usuários**: convidar com perfil (link de 48 h), redefinir senha, bloquear. Usuário comum não vê esta tela (403 na API).
7. Menu do usuário → **Modo escuro** (mesmo design, contraste AA).

**2:40–3:00 · Fechamento**
> "SGD só leitura, nomes nunca saem para a IA, roda local com um comando. De horas de ligações para segundos."

**Plano B (se algo falhar)**
- IA fora do ar → o app avisa e usa o score determinístico (sem quebrar).
- Postgres fora → o app usa o snapshot SQLite automaticamente (o selo no topo mostra a fonte).
- Interface antiga de uma página em http://localhost:8000/legado.
- Briefing alternativo: `briefing_app_mobile_EXEMPLO.txt` (React Native/TypeScript/Node, 6 meses, 100%).
