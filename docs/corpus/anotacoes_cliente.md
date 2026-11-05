# Anotações do cliente — VINT GLOBAL (desafio do hackathon)

## Problema
Como alocar o talento certo na hora certa? Hoje o processo é manual e lento: quando chega um projeto, alguém consulta o SGD, lista colaboradores com as skills necessárias e clica um a um verificando disponibilidade nos próximos 3 meses. Quando não acha, ou quando o dado está desatualizado, começa uma sequência de ligações e mensagens para líderes. Resultado: tempo perdido e baixa assertividade.

## Solução esperada
Uma automação integrada ao banco + IA que recebe um "prompt" do usuário (requisitos do projeto) e devolve, em minutos, o melhor matchmaking entre os talentos disponíveis — sem busca manual.

## Bases a integrar
1. SGD (preferencial; nas anotações aparecia também como "SGB" — é o mesmo sistema, nome oficial SGD): nome do colaborador, skills, projetos alocados, disponibilidade e tempo gasto no projeto atual, duração do projeto.
2. Base de talentos externa (iHiring / InHire): candidatos externos. Na base recebida corresponde às tabelas `talentos` e `talento_skills`, com dados sintéticos de teste.

## Entrada do usuário
- Skills necessárias
- Duração / tempo necessário do projeto
- Disponibilidade requerida
- Texto livre descrevendo o projeto e suas características
- (Opcional) upload de documento PDF/DOCX com o briefing do projeto; a IA lê e extrai os requisitos automaticamente

## Saída esperada
- Ranking de candidatos com score de match, justificativa curta e disponibilidade no período
- Cruzamento com histórico de projetos do candidato (já participou de algo parecido?)
- Flag de remanejamento: sinalizar quando o candidato aparece 100% alocado mas é o mais viável, mostrando o que precisaria ser remanejado
- Sugestão de PDI (Plano de Desenvolvimento Individual) para candidatos próximos do ideal
- Busca semântica (RAG) sobre a documentação e sobre descrições de projetos e skills

## Requisitos não funcionais
- Não exigir entrada manual de dados: tudo que é dado do colaborador vem do banco
- Decisão em minutos
- Cor principal da interface: roxo VINT GLOBAL #8233E0
- A empresa usa Cursor AI; a solução deve rodar facilmente local no hackathon
- Banco somente leitura; dados pessoais tratados como sensíveis (LGPD)
