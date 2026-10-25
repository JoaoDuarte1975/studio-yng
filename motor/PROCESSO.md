# Studio YNG · Como funciona

## Peças
- Painel Studio YNG (artefacto): https://claude.ai/artifact/NaeQyJRWdwQfmKCdEj2Qhc. Lista as apresentações e tem os botões.
- Pasta OneDrive `Studio YNG`:
  - `Apresentações/<nome>/`: a ficha `Apresentação.xlsx`, a pasta `Media` (vídeos e imagens) e `_desenhos` (criada pelo sistema).
  - `Apresentações/_Modelo/`: ficha em branco, de referência.
  - `_Sistema/motor/`: gerar.py, template.html, GUIA-DESENHO.md, TAREFA.md. `_Sistema/marca/`: logótipos e cores de cada marca.
- Tarefa agendada "Studio YNG" (conta do JD, PC do JD, sem horário): faz o trabalho quando um botão a dispara. Instruções em TAREFA.md.
- Repositório GitHub `JoaoDuarte1975/studio-yng`, GitHub Pages: link do cliente `/<id>/`, draft interno `/drafts/<id>-<chave>/`. O ramo `motor` guarda a cópia do motor.

## Circuito
1. Nova apresentação (painel): o sistema cria a pasta e a ficha. Estado: Ficha por preencher.
2. Preencher a ficha: blocos, Ideias, o Claude no Excel escreve os textos (folha "Claude"), vídeos na Media.
3. Gerar draft (painel): desenha, traduz, gera a pré-visualização interna com a senha draft, email. Repetível. Para pedir mudanças: "Comentar draft" no painel (o sistema aplica os comentários no draft seguinte e regista-os na ficha, em "Como deve ficar") ou corrigir a ficha.
4. Publicar (painel): só a partir de um draft. Se a ficha ou a Media mudaram depois do draft, recusa e pede draft novo. Sai o link do cliente com a senha do cliente, email.

## Limites
- O disparo imediato funciona com a conta do JD. Pedidos de colegas ficam registados e arrancam quando o JD abre o painel.
- O PC do JD tem de estar ligado, com o Claude aberto e o OneDrive sincronizado.
- Se a ficha estiver aberta no Excel, o sistema não a consegue gravar: fechar e carregar outra vez no botão.
- Vídeos acima de 95 MB depois de comprimidos não entram (limite do GitHub).
- Repositório público: os textos vão cifrados, mas vídeos e imagens ficam acessíveis a quem souber o endereço exato.
