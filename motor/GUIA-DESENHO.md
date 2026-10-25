# Guia de desenho das secções (para o Claude que gera)

Cada secção da apresentação é desenhada à medida a partir do briefing (`gerar.py briefing`).
A moldura (entrada com senha, idiomas, menu, modo página/reel, modal, publicação) é fixa e não se mexe.

## O que se entrega
- Um ficheiro por secção: `_desenhos/cena-secao-<n>.html` (o nome vem no campo `ficheiro` do briefing).
- Se `one_page` for verdadeiro: `desenhos/resumo.html`, uma folha A4 (210 x 297 mm) com o essencial da apresentação.
- Cada ficheiro é um **fragmento**: sem `<html>`, `<head>` ou `<body>`. Vai dentro de `<section class="scene">`.

## Regras
1. Conteúdo: usar só o que está no briefing. Não inventar números, nomes, datas nem resultados. Se faltar algo, deixar de fora.
2. Idiomas: todo o texto visível em todos os idiomas do briefing, assim:
   `<span data-l="pt">Texto</span><span data-l="en">Text</span>`. Se a coluna EN vier preenchida, usar essa; senão traduzir.
   Português de Portugal. Sem travessões (usar vírgulas, dois pontos, parênteses).
3. Media: escrever `src="media:NOME-DO-FICHEIRO"` exatamente como está no Excel. O gerador troca pelo caminho final.
   Vídeos de fundo: `<video src="media:x.mp4" muted loop playsinline data-auto></video>`.
   Para abrir em grande ao clicar: qualquer elemento com `data-open="media:x.mp4"`.
4. Estilo: usar as variáveis e classes da moldura, para tudo ficar coerente:
   - cores `var(--a)` (principal), `var(--b)`, `var(--ink)`, `var(--soft)`, `var(--mute)`, `var(--line)`, `var(--card)`, `var(--bg2)`
   - letras `var(--sans)`, `var(--mono)`; classe `disp` para títulos condensados em maiúsculas
   - estrutura `<div class="inner">…</div>` (largura máxima e margens); `kick`, `ttl`, `ttl sm`, `txt`, `card`, `grid`, `tag`, `num`
   - animação de entrada: classe `rv` em cada bloco que deve aparecer ao entrar no ecrã
   - CSS próprio da secção: `<style>` no início do fragmento, com tudo prefixado pela classe do campo `classe` do briefing (ex.: `.c-secao-2`), que a moldura põe na secção. Nunca `#s<n>`: a ordem pode mudar.
5. Interação: `<script>` no fim do fragmento, em JavaScript simples, sem bibliotecas externas, só a mexer dentro da própria secção.
6. Telemóvel: tem de funcionar a 375 px de largura, sem scroll horizontal.
7. Formato reel: a secção ocupa um ecrã; cabe sem scroll num portátil (1366 x 768).
8. "Tipo de bloco" é a base do desenho (o bloco do catálogo com o mesmo nome é a referência mínima de qualidade);
   desenha-se a versão à medida para esta apresentação. Tipo "livre": não há referência, segue-se só "Como deve ficar".
9. "Como deve ficar" manda. Se contradisser o conteúdo, segue-se o conteúdo e regista-se aviso.

## Depois de desenhar
Correr `gerar.py construir … --desenhos desenhos/`, abrir o resultado no browser a 1366 px e a 375 px, nos dois idiomas, e corrigir antes de publicar.

## Logótipos
`src="media:@logo"` = logótipo YNG da apresentação (o do Excel ou o branco por defeito). `src="media:@logo2"` = logótipo do cliente.
Se não houver logótipo do cliente, não pôr o elemento.
