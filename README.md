# Do projeto

Este repositório faz parte do projeto de ciclo 4 da equipe 4 do primeiro ano do ensino médio. Faz chamadas à API do *OpenRouter* segundo os modelos de prompt de política e avaliação, repetindo as chamadas até aprovação. Contém uma TUI para entrada e apresentação da saída.

# Preparação

- Clone este repositório.
- Instale as dependências descritas na próxima seção.
- Crie um arquivo chamado **key.txt** dentro da pasta clonada.
- Acesse o site https://openrouter.ai/.
- Crie uma chave de API na seção **Chaves** e guarde-a.
- Acrescente créditos caso quiser utilizar modelos pagos.
- Insira a chave de API no **key.txt**, sem espaços nem quebras de linha.

# Dependências

- *Textual>=6.4.0*
- *openai>=2.6.1*
- *requests*

# Utilização

- Execute o programa **tui.py**.
- Selecione o modelo desejado.
- Descreva os valores empresariais desejados.
- Explique a situação e contexto.
- Pressione enviar e espere até a resposta.
- Acesse a aba saída.
- A primeira caixa representa o plano de ação.
- As quatro próximas indicam a avaliação.
- A aba extensível indica a sequência de prompts e respostas.