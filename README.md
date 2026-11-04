# 🎵 Empório da Música — Lira

**Lira** é a agente de atendimento por mensagens de texto do Empório da Música, loja de instrumentos musicais em Campo Grande/MS.

> Democratizar o acesso a instrumentos musicais de qualidade na região Centro-Oeste, oferecendo atendimento especializado e preços competitivos, contribuindo para o desenvolvimento cultural e musical da comunidade.

## Desafio Técnico — AI Engineer @ Artefact

### Decisões de Arquitetura

| Decisão | Escolha | Justificativa |
|---------|---------|---------------|
| Acesso a dados | Function calling | Dados pequenos (65 produtos, 20 pedidos). Text-to-SQL adiciona complexidade sem ganho |
| Políticas da loja | System prompt | Documento curto (~8 páginas). RAG com embeddings não se justifica |
| Tratamento de dados | Nenhum pipeline ETL | Dados fornecidos já estão limpos e consistentes |

### Estrutura
artefact_2/
├── data/ # CSVs e PDF de políticas
├── prompts/ # System prompt versionado
├── tools/ # Implementação das functions
├── examples/ # 3-5 conversas exemplo
├── tests/ # Harness de testes/eval
├── notebooks/ # EDA e análise exploratória
├── agent.py # Orquestrador principal
├── config.py # Configurações
└── requirements.txt


## Status

🚧 Em desenvolvimento

## Contato

suporte: contato@emporiodamusica.com.br
