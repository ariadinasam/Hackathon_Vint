# O que falta para o MVP ficar 100%

Legenda: 🔴 bloqueia a demo/uso real · 🟠 importante · 🟡 melhoria

## Validar no seu computador (não deu para testar daqui)
- 🟠 **IA no dia da apresentação** — a chave do Gemini funciona; as falhas foram **503 “alta demanda”** do Google no modelo
  `gemini-3.8-flash`. O app agora tenta de novo, usa modelos reserva do Gemini e, se houver `GROQ_API_KEY`, cai no Groq.
  Recomendado: criar a chave grátis do Groq e testar uma busca antes da banca.
- 🔴 **Postgres do Docker** — testado só com o snapshot SQLite. Suba `docker compose up -d` na pasta do hackathon e confira
  no resultado “fonte SGD: Postgres”.
- 🟠 **Navegador real** — telas verificadas com dados pseudonimizados; vale clicar o fluxo completo uma vez antes da banca.

## Dados que não existem no SGD recebido
- 🟠 **E-mail, gestor direto, squad e cidade do colaborador** → a ficha mostra “Não consta no SGD” e usa o gerente da
  demanda atual. Precisa de integração com RH/AD.
- 🟠 **Descrição textual das demandas** (hoje “Demanda N”) → “projeto parecido” usa skills + tipo de serviço + metodologia.
- 🟠 **Catálogo de cursos/trilhas (LNC)** → o PDI sugere skill, prazo estimado, mentor interno e demanda para praticar,
  mas não um curso real.
- 🟠 **iHiring/InHire real** → a base recebida é sintética (sem anos de experiência, data de início, contato).
  Precisa da API do InHire.
- 🟡 **Planejamento só até fev/2027** → meses depois aparecem 100% livres (o app avisa).

## Produto
- 🔴 **Envio de e-mail** (convite, redefinição, “esqueci minha senha”) → hoje o Admin copia o link. Precisa SMTP/Microsoft 365.
- 🟠 **Efetivar a alocação no SGD** → a decisão fica registrada no app (o SGD é somente leitura por regra do desafio).
  Próximo passo: exportar/integrar com o fluxo de aprovação do SGD.
- 🟠 **Avisar gestores afetados pelo remanejamento** (hoje o card diz com quem falar).
- 🟡 Comentários na busca, comparar 2–3 candidatos lado a lado, exportar PDF do resultado, histórico de alterações do projeto.

## Técnico / segurança
- 🟠 HTTPS + `COOKIE_SECURE=1`, deploy (container do app), backup do `data/app.db`.
- 🟠 Limite de tentativas por IP e trilha de auditoria (quem viu/selecionou quem).
- 🟡 Testes de interface automatizados (Playwright) e CI; embeddings reais para a base de conhecimento.
- 🟡 Política de retenção LGPD para o `app.db` (guarda resultados com nomes do SGD).
