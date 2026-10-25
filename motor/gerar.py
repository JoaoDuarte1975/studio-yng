#!/usr/bin/env python3
"""Studio YNG · gerador de apresentações.

Excel (backoffice) + pasta Media  ->  pasta publicável (index.html + media/).

Estrutura do Excel:
  Instruções       como preencher
  Configuração     título, marca, senha, idiomas, estado...
  Conteúdo         12 quadros de secção; em cada um escolhe-se o bloco e os rótulos da tabela mudam com ele
  _Blocos          catálogo escondido que alimenta a lista e os rótulos

Comandos:
  gerar.py modelo    SAIDA.xlsx [--exemplo EXEMPLO.json]
  gerar.py validar   APRESENTACAO.xlsx [--media DIR]
  gerar.py briefing  APRESENTACAO.xlsx            conteúdo de cada secção, para o Claude desenhar
  gerar.py pendentes APRESENTACAO.xlsx            {chave: texto PT} do que falta traduzir
  gerar.py traduzir  APRESENTACAO.xlsx TRAD.json  escreve as traduções nas colunas EN do Excel
  gerar.py construir APRESENTACAO.xlsx --media DIR --saida DIR [--desenhos DIR]
  gerar.py procurar  PASTA_APRESENTACOES          Excel com Estado = Publicar
  gerar.py estado    APRESENTACAO.xlsx "Campo=valor" ...
"""
import argparse, base64, json, os, re, shutil, subprocess, sys, unicodedata, urllib.request
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

AQUI = Path(__file__).resolve().parent
TEMPLATE = AQUI / "template.html"
DIR_MARCAS = AQUI.parent / "marca"
try: MARCAS = json.load(open(DIR_MARCAS / "marcas.json", encoding="utf-8"))
except Exception: MARCAS = {"YoungNetwork Group": {"pasta": "yng", "cor1": "#E74F3D", "cor2": "#0044FF", "fundo": "#080808", "fundo2": "#141414"}}

# ------------------------------------------------------------------ catálogo de blocos
# Cada bloco = uma folha do Excel. "cab" = campos de cabeçalho; "tab" = colunas da lista (rótulo, campo interno, traduz?, ajuda, exemplo)
K, T, X, F, P = "Pequeno título", "Título", "Texto", "Ficheiro ou link", "Como deve ficar"
CAB_BASE = [(K, "kicker", True, "Linha curta por cima do título (ex.: PROPOSTA 2027)."),
            (T, "title", True, "Título da secção."),
            (X, "text", True, "Texto corrido (opcional)."),
            (P, "pedido", False, "Opcional: o que quer neste bloco (ex.: 'vídeo à esquerda, números à direita').")]
CAB_MEDIA = (F, "media", False, "Vídeo ou imagem de fundo: nome do ficheiro na pasta Media ou link (YouTube, Vimeo, OneDrive).")

BLOCOS = {
 "Capa": {"tipo": "abertura", "desc": "Primeiro ecrã: logótipos, título grande e vídeo ou imagem de fundo.",
          "cab": [CAB_BASE[0], CAB_BASE[1], CAB_BASE[2], CAB_MEDIA, CAB_BASE[3]], "tab": [],
          "ex": {K: "Proposta 2027", T: "Lançamos a marca em 30 dias.", F: "video-fundo.mp4"}},
 "Frase de impacto": {"tipo": "hero", "desc": "Uma frase grande, sozinha, por cima de um vídeo ou imagem.",
          "cab": [CAB_BASE[0], CAB_BASE[1], CAB_BASE[2], CAB_MEDIA, CAB_BASE[3]], "tab": []},
 "Texto e imagem": {"tipo": "texto", "desc": "Título e texto, com uma imagem ou vídeo ao lado (opcional).",
          "cab": [CAB_BASE[0], CAB_BASE[1], CAB_BASE[2], (F, "media", False, "Imagem ou vídeo ao lado do texto (opcional)."), CAB_BASE[3]], "tab": []},
 "Números": {"tipo": "numeros", "desc": "Números grandes em destaque (resultados, alcance, anos).",
          "cab": CAB_BASE, "tab": [("Número", "value", False, "Ex.: 68.268 ou 245,7K ou +139%", "68.268"),
                                   ("O que mede", "title", True, "Ex.: pico de espectadores", "pico de espectadores"),
                                   ("Nota", "text", True, "Opcional", "")]},
 "Vídeos e trabalhos": {"tipo": "cases", "desc": "Grelha de trabalhos; ao clicar, o vídeo abre em grande.",
          "cab": CAB_BASE, "tab": [(F, "media", False, "Vídeo ou imagem do trabalho: ficheiro na Media ou link", "case-galp.mp4"),
                                   ("Imagem de capa", "poster", False, "Opcional: imagem a mostrar antes de o vídeo tocar", ""),
                                   ("Cliente ou categoria", "sub", True, "Linha pequena por cima do título", "Galp"),
                                   (T, "title", True, "Nome do trabalho", "Campanha de verão"),
                                   ("Descrição", "text", True, "Opcional", "")]},
 "Equipa": {"tipo": "equipa", "desc": "Fotografias com nome e função.",
          "cab": CAB_BASE, "tab": [("Fotografia", "media", False, "Ficheiro na Media ou link", "ana.jpg"),
                                   ("Nome", "title", False, "", "Ana Silva"),
                                   ("Função", "sub", True, "", "Diretora criativa"),
                                   ("Nota", "text", True, "Opcional", "")]},
 "Lista": {"tipo": "lista", "desc": "Blocos numerados: serviços, formatos, fases, passos.",
          "cab": CAB_BASE, "tab": [(T, "title", True, "", "Estratégia"), ("Subtítulo", "sub", True, "Opcional", ""),
                                   (X, "text", True, "", "Plano de comunicação e calendário.")]},
 "Logótipos": {"tipo": "logos", "desc": "Logótipos de clientes ou parceiros.",
          "cab": CAB_BASE, "tab": [(F, "media", False, "Logótipo (PNG transparente ou SVG) na Media ou link", "galp.png"),
                                   ("Nome", "title", False, "Aparece se faltar o logótipo", "Galp")]},
 "Contactos": {"tipo": "contacto", "desc": "Pessoas de contacto, com email e WhatsApp.",
          "cab": CAB_BASE, "tab": [("Nome", "title", False, "", "JD"), ("Função", "sub", True, "", "CEO · YoungNetwork Group"),
                                   ("Email", "email", False, "", "nome@youngnetworkgroup.com"),
                                   ("Telefone", "phone", False, "Com indicativo (ex.: +351 912 345 678)", ""),
                                   ("Link", "link", False, "Opcional", "")]},
 "Vídeo grande": {"tipo": "video", "desc": "Um vídeo em ecrã inteiro. No reel, avança quando o vídeo acaba.",
          "cab": [CAB_BASE[0], CAB_BASE[1], (F, "media", False, "O vídeo: ficheiro na Media ou link (YouTube, Vimeo, OneDrive)."), CAB_BASE[3]], "tab": []},
 "Cartões com filtro": {"tipo": "cartoes", "desc": "Cartões com botões de filtro em cima (ex.: entregas por momento).",
          "cab": CAB_BASE, "tab": [("Filtro", "tag", True, "Os cartões com o mesmo filtro ficam juntos", "Semana 1"),
                                   ("Categoria", "sub", True, "Etiqueta pequena", "Social"),
                                   (T, "title", True, "", "Peças para redes"), (X, "text", True, "", "Posts e stories."),
                                   ("Número", "value", False, "Opcional: número em destaque", "12"),
                                   ("Unidade", "goal", True, "Opcional: ao lado do número (ex.: por mês)", "por mês")]},
 "Calendário": {"tipo": "calendario", "desc": "Dias ou fases de um evento ou projeto.",
          "cab": CAB_BASE, "tab": [("Dia ou data", "value", False, "Aparece em grande (ex.: 24 ou S1)", "24"),
                                   ("Dia da semana", "sub", True, "Opcional (ex.: SÁB · OUT)", "SÁB · OUT"),
                                   ("O que acontece", "title", True, "", "Ronda 1"), ("Descrição", "text", True, "Opcional", ""),
                                   ("Fase", "tag", True, "Opcional: dias da mesma fase ficam com a mesma cor", "Fase de grupos")]},
 "Tarefas": {"tipo": "tarefas", "desc": "Quem faz o quê e até quando.",
          "cab": CAB_BASE, "tab": [("Quando", "value", False, "", "até 31/10"), ("Quem", "sub", True, "", "YoungNetwork"),
                                   ("O quê", "text", True, "", "Contrato assinado.")]},
 "Progresso": {"tipo": "barras", "desc": "Barras de progresso: valor atual contra uma meta.",
          "cab": CAB_BASE, "tab": [("Indicador", "title", True, "", "Stories"), ("Valor atual", "value", False, "Número", "34"),
                                   ("Meta", "goal", False, "Número", "48"), ("Nota", "text", True, "Opcional", "")]},
 "Perguntas": {"tipo": "perguntas", "desc": "Cartões que viram ao tocar: pergunta à frente, resposta atrás.",
          "cab": CAB_BASE, "tab": [("Pergunta", "title", True, "", "Como foi o jogo?"), ("Pista", "sub", True, "Opcional, por baixo da pergunta", ""),
                                   ("Resposta", "text", True, "Aparece ao virar", "")]},
 "Checklist": {"tipo": "checklist", "desc": "Listas para ir marcando (ficam gravadas no telemóvel de quem usa).",
          "cab": CAB_BASE, "tab": [("Grupo", "title", True, "Nome do grupo de tarefas", "Antes do jogo"),
                                   ("Etiqueta", "tag", True, "Opcional", ""),
                                   ("Itens a marcar", "text", True, "Um por linha (Alt+Enter para mudar de linha)", "Montar câmara\nTestar som")]},
 "Princípios": {"tipo": "regras", "desc": "Regras, princípios ou compromissos, em cartões.",
          "cab": CAB_BASE, "tab": [(T, "title", True, "", "Resultado só depois do jogo"), (X, "text", True, "", "")]},
 "Galeria": {"tipo": "galeria", "desc": "Imagens e vídeos em mosaico; abrem em grande ao clicar.",
          "cab": CAB_BASE, "tab": [(F, "media", False, "Ficheiro na Media ou link", "foto1.jpg"), ("Legenda", "title", True, "Opcional", "")]},
 "Bloco livre": {"tipo": "livre", "desc": "Quando nenhum bloco serve: descreva em 'Como deve ficar' e é desenhado à medida.",
          "cab": [CAB_BASE[0], CAB_BASE[1], CAB_BASE[2], CAB_MEDIA,
                  (P, "pedido", False, "OBRIGATÓRIO: descreva o que quer ver (ex.: 'mapa com os 5 países e o número de eventos em cada').")],
          "tab": [(T, "title", True, "", ""), (X, "text", True, "", ""), ("Número", "value", False, "", ""),
                  (F, "media", False, "", ""), ("Link", "link", False, "", "")]},
}
TIPO_PARA_BLOCO = {b["tipo"]: n for n, b in BLOCOS.items()}

ESTADOS = ["Ficha", "Draft", "Publicado", "Erro"]
IDIOMAS = ["PT+EN", "PT", "PT+EN+ES", "EN"]
FORMATOS = ["Página", "Reel"]
SELETOR_CORES = "https://htmlcolorcodes.com/color-picker/"
PAINEL = "https://claude.ai/artifact/NaeQyJRWdwQfmKCdEj2Qhc"

CONFIG = [
    ("Título PT", "Título da apresentação (aparece na entrada e no separador do browser).", ""),
    ("Título EN", "Deixe em branco: é traduzido automaticamente.", ""),
    ("Barra PT", "Texto curto no topo das páginas (ex.: YOUNGNETWORK · PROPOSTA 2027).", ""),
    ("Barra EN", "Deixe em branco: é traduzido automaticamente.", ""),
    ("Cliente", "Nome do cliente ou destinatário.", ""),
    ("Endereço", "Parte final do link, sem espaços nem acentos (ex.: galp-2027). Em branco = criado a partir do título.", ""),
    ("Marca", "Marca que assina: define logótipo, cores e fundo.", "YoungNetwork Group"),
    ("Com senha", "S (por defeito) = só abre com senha. N = aberta a quem tiver o link.", "S"),
    ("Senha", "Em branco = o sistema cria uma, escreve-a aqui e envia-a no email.", ""),
    ("Formato", "Página = página de scroll com menu no topo. Reel = ecrãs em sequência que correm como um vídeo.", "Página"),
    ("Idiomas", "Idiomas com botão. O primeiro é o de abertura.", "PT+EN"),
    ("Reprodução automática", "Só no Reel. S = abre a correr como um vídeo; N = abre parado, ecrã a ecrã.", "S"),
    ("One page resumo", "S (por defeito) = gera também uma página de resumo (ecrã e PDF A4).", "S"),
    ("Cor principal", "Só para trocar a cor da marca. Tem de ser código hexadecimal (ex.: #E30613); seletor de cores no link desta célula. "
                      "Pantone não serve: a conversão Pantone para ecrã é sempre aproximada e não há tabela oficial que o sistema possa usar. "
                      "Se só tiver o Pantone, tire o hexadecimal do brand kit (os nossos têm os dois) ou do site da Pantone.", ""),
    ("Cor secundária", "Só para trocar a segunda cor da marca (hexadecimal).", ""),
    ("Logo da marca", "Só para usar outro logótipo (ficheiro na pasta Media). Em branco = logótipo da marca.", ""),
    ("Logo cliente", "Logótipo do cliente (ficheiro na pasta Media ou link). Opcional.", ""),
    ("Pedido por", "Email de quem pede. Recebe o link e a senha quando estiver publicada.", ""),
    ("Estado", "Preenchido automaticamente: Ficha (por preencher), Draft (pré-visualização gerada), Publicado, Erro. Os botões estão no Studio YNG.", "Ficha"),
    ("Senha draft", "Senha interna da pré-visualização. Preenchida automaticamente; nunca a dê ao cliente.", ""),
    ("Link draft", "Pré-visualização interna. Preenchido automaticamente.", ""),
    ("Draft gerado em", "Preenchido automaticamente.", ""),
    ("Link publicado", "Link final do cliente. Preenchido automaticamente.", ""),
    ("Publicado em", "Data e hora da última publicação. Preenchido automaticamente.", ""),
    ("Mensagem do sistema", "Preenchido automaticamente (erros e avisos).", ""),
]
AUTO = {"Título EN", "Barra EN", "Senha draft", "Link draft", "Draft gerado em", "Link publicado", "Publicado em", "Mensagem do sistema", "Estado"}
ESQUELETO = [("Capa", ""), ("Texto e imagem", "Quem somos"), ("Números", "Resultados"),
             ("Vídeos e trabalhos", "Trabalhos"), ("Equipa", "Equipa"), ("Contactos", "Contactos")]

AZUL = "1F2937"; AMAR = "FFF7D6"; LIL = "EEF2FF"; CINZA = "9CA3AF"; SECC = "E74F3D"
fino = Side(style="thin", color="D1D5DB")
BORDA = Border(left=fino, right=fino, top=fino, bottom=fino)

# ---- folha Conteúdo: quadros de secção empilhados
N_SECCOES = 12
N_ELEM = 15
SLOTS = 7                      # colunas de elementos (B..H); EN em I..O
ALTURA = 3 + 6 + 1 + N_ELEM + 2  # linhas por quadro
CAMPOS_CAB = [("Ideias", "ideias", False, "Escreva aqui as ideias soltas, em bruto. Depois peça ao Claude (no painel do Claude no Excel) para escrever os textos: ver folha 'Claude'."),
              (K, "kicker", True, "Linha curta por cima do título (ex.: PROPOSTA 2027)."),
              (T, "title", True, "Título da secção."),
              (X, "text", True, "Texto corrido (opcional)."),
              (F, "media", False, "Vídeo ou imagem de fundo ou ao lado: ficheiro na pasta Media ou link (YouTube, Vimeo, OneDrive)."),
              (P, "pedido", False, "Opcional: como quer o bloco (ex.: 'vídeo à esquerda, números à direita'). No Bloco livre é obrigatório.")]
FOLHA = "Conteúdo"

def _r0(n): return 4 + (n - 1) * ALTURA      # linha do título "SECÇÃO n" (linhas 1-2: aviso)


# ------------------------------------------------------------------ modelo
def _h(c, cor=AZUL):
    c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor=cor)
    c.alignment = Alignment(wrap_text=True, vertical="center")

def _quadro(ws, n, sec=None):
    from openpyxl.formatting.rule import FormulaRule
    sec = sec or {}
    r = _r0(n)
    for j in range(1, 16): ws.cell(r, j).fill = PatternFill("solid", fgColor=AZUL)
    ws.cell(r, 1, f"SECÇÃO {n}").font = Font(bold=True, size=13, color="FFFFFF")
    bl = ws.cell(r, 2, sec.get("Bloco")); bl.fill = PatternFill("solid", fgColor=AMAR); bl.font = Font(bold=True, size=12); bl.border = BORDA
    for col, txt in ((3, "Incluir"), (5, "Nome no menu"), (8, "Ordem"), (10, "Duração no reel (s)")):
        ws.cell(r, col, txt).font = Font(bold=True, color="FFFFFF"); ws.cell(r, col).alignment = Alignment(horizontal="right")
    for col, val, cor in ((4, sec.get("Incluir", "S"), AMAR), (6, sec.get("Nome no menu"), AMAR), (7, sec.get("Nome no menu EN"), LIL),
                          (9, sec.get("Ordem", n), AMAR), (11, sec.get("Duração no reel (s)"), AMAR)):
        c = ws.cell(r, col, val); c.fill = PatternFill("solid", fgColor=cor); c.border = BORDA
    # ajuda que muda com o bloco
    f = ws.cell(r + 1, 2, f'=IF($B${r}="","⬅ Escolha o bloco na célula amarela ao lado de SECÇÃO {n}. Deixe vazio se não precisar desta secção.",'
                          f'IFERROR(VLOOKUP($B${r},_Blocos!$A:$B,2,FALSE),"Bloco desconhecido: escolha um da lista."))')
    f.font = Font(italic=True, color="374151"); ws.merge_cells(start_row=r + 1, start_column=2, end_row=r + 1, end_column=15)
    ws.cell(r + 1, 1, "Este bloco").font = Font(bold=True, color="6B7280")
    # cabeçalho da secção
    ws.cell(r + 2, 1, "Campo").font = Font(bold=True, color="6B7280")
    ws.cell(r + 2, 2, "Português").font = Font(bold=True, color="6B7280")
    ws.cell(r + 2, 3, "Inglês (automático)").font = Font(bold=True, color="6B7280")
    ws.cell(r + 2, 4, "Ajuda").font = Font(bold=True, color="6B7280")
    cab = sec.get("cab", {})
    for i, (rot, campo, traduz, ajuda) in enumerate(CAMPOS_CAB):
        rr = r + 3 + i
        ws.cell(rr, 1, rot).font = Font(bold=True)
        c = ws.cell(rr, 2, cab.get(rot)); c.fill = PatternFill("solid", fgColor=AMAR); c.border = BORDA; c.alignment = Alignment(wrap_text=True, vertical="top")
        if traduz: c = ws.cell(rr, 3); c.fill = PatternFill("solid", fgColor=LIL); c.border = BORDA
        else: ws.cell(rr, 3, "não se traduz").font = Font(italic=True, color=CINZA)
        ws.cell(rr, 4, ajuda).font = Font(italic=True, size=9, color="6B7280")
        ws.merge_cells(start_row=rr, start_column=4, end_row=rr, end_column=15)
    # tabela de elementos: rótulos vêm do bloco escolhido
    rh = r + 3 + len(CAMPOS_CAB)
    _h(ws.cell(rh, 1, "Incluir"))
    for k in range(SLOTS):
        col = 2 + k
        c = ws.cell(rh, col, f'=IF($B${r}="","",IFERROR(INDEX(_Blocos!{get_column_letter(3 + k)}:{get_column_letter(3 + k)},MATCH($B${r},_Blocos!$A:$A,0))&"",""))')
        _h(c)
        e = ws.cell(rh, col + SLOTS, f'=IF($B${r}="","",IFERROR(INDEX(_Blocos!{get_column_letter(3 + SLOTS + k)}:{get_column_letter(3 + SLOTS + k)},MATCH($B${r},_Blocos!$A:$A,0))&"",""))')
        _h(e, "4F46E5")
    lista = sec.get("lista", [])
    base = _base(sec.get("Bloco") or "") if sec.get("Bloco") else None
    rot_slot = [t[0] for t in BLOCOS[base]["tab"]] if base else []
    for i in range(N_ELEM):
        rr = rh + 1 + i
        item = lista[i] if i < len(lista) else {}
        ws.cell(rr, 1, item.get("Incluir")).border = BORDA
        for k in range(SLOTS * 2):
            c = ws.cell(rr, 2 + k); c.border = BORDA; c.alignment = Alignment(wrap_text=True, vertical="top")
            if k >= SLOTS: c.fill = PatternFill("solid", fgColor=LIL)
        for rot, val in item.items():
            if rot in rot_slot: ws.cell(rr, 2 + rot_slot.index(rot), val)
    # colunas não usadas pelo bloco: cinzento
    ws.conditional_formatting.add(f"B{rh + 1}:{get_column_letter(1 + SLOTS * 2)}{rh + N_ELEM}",
                                  FormulaRule(formula=[f'B${rh}=""'], fill=PatternFill("solid", fgColor="E5E7EB")))
    dv = DataValidation(type="list", formula1='"S,N"', allow_blank=True); ws.add_data_validation(dv)
    dv.add(f"D{r}"); dv.add(f"A{rh + 1}:A{rh + N_ELEM}")

TOM = {
 "YoungNetwork Group": "Tom de voz YoungNetwork: ousado, criativo e confiante; frases curtas e impactantes; verbos no presente; "
                       "direto, sem rodeios nem formalidade a mais; energia e atitude, sem exageros vazios. Assinatura: Leading Brave Brands.",
}
PEDIDO_CLAUDE = """Escreve os textos desta apresentação a partir das ideias.

Regras:
1. Trabalha só na folha Conteúdo. Para cada SECÇÃO com bloco escolhido e com o campo 'Ideias' preenchido:
   escreve Pequeno título, Título e Texto (coluna Português) e preenche as linhas da tabela por baixo,
   respeitando os nomes das colunas que lá aparecem (mudam conforme o bloco).
2. Usa só o que está nas Ideias. Não inventes números, nomes, datas, clientes nem resultados. Se faltar informação, deixa em branco e escreve o que falta numa nota na própria célula de Ideias.
3. Português de Portugal. Sem travessões: usa vírgulas, dois pontos ou parênteses.
4. Títulos curtos (até 8 palavras). Pequeno título até 4 palavras. Texto até 40 palavras.
5. {tom}
6. Não mexas nas colunas de inglês (lilás), na folha Configuração, nas células cinzentas nem nas fórmulas.
7. No fim, diz-me em tópicos o que escreveste e o que ficou por preencher."""

def _folha_claude(wb, marca):
    ws = wb.create_sheet("Claude")
    ws["A1"] = "PEDIDO PARA O CLAUDE NO EXCEL"; ws["A1"].font = Font(bold=True, size=14, color=AZUL)
    ws["A2"] = "1. Preencha o campo 'Ideias' nas secções da folha Conteúdo.  2. Abra o painel do Claude no Excel.  3. Copie a célula A4 e cole no Claude.  4. Reveja o que ele escreveu."
    ws["A2"].font = Font(italic=True, color="6B7280")
    tom = TOM.get(marca) or f"Tom de voz da marca {marca}: profissional, claro e direto."
    c = ws.cell(4, 1, PEDIDO_CLAUDE.format(tom=tom)); c.alignment = Alignment(wrap_text=True, vertical="top")
    c.fill = PatternFill("solid", fgColor=AMAR); c.border = BORDA
    ws.column_dimensions["A"].width = 120; ws.row_dimensions[4].height = 300

def criar_modelo(saida, exemplo=None):
    exemplo = exemplo or {}
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "Instruções"
    linhas = [
        ("STUDIO YNG · COMO FAZER UMA APRESENTAÇÃO", "t"),
        ("", ""),
        ("1. DE ONDE VEM ESTE EXCEL", "s"),
        ("   Foi criado pelo Studio YNG (" + PAINEL + ") quando alguém carregou em 'Nova apresentação'.", ""),
        ("   Está em Studio YNG > Apresentações > <nome>.", ""),
        ("   Na mesma pasta há a pasta Media, para vídeos e imagens. Não mude nomes nem mova o Excel.", ""),
        ("", ""),
        ("2. VÍDEOS, IMAGENS E LOGÓTIPOS", "s"),
        ("   Em todas as células 'Ficheiro ou link' pode pôr:", ""),
        ("   a. o nome de um ficheiro que pôs na pasta Media (ex.: case-galp.mp4), ou", ""),
        ("   b. um link do YouTube, Vimeo ou OneDrive/SharePoint. YouTube e Vimeo ficam embutidos; OneDrive é descarregado ao publicar.", ""),
        ("", ""),
        ("3. FOLHA CONFIGURAÇÃO", "s"),
        ("   Título, cliente, marca (YoungNetwork Group, Taylor, Alice...), senha, idiomas, formato (página ou reel).", ""),
        ("", ""),
        ("4. FOLHA CONTEÚDO", "s"),
        ("   Tem 12 quadros (Secção 1 a 12), de cima para baixo. Cada quadro é uma secção da apresentação.", ""),
        ("   a. Na célula amarela ao lado de 'SECÇÃO' escolha o bloco na lista (Capa, Números, Calendário, Equipa...).", ""),
        ("      Logo por baixo aparece o que esse bloco faz e o que preencher.", ""),
        ("   b. Preencha Pequeno título, Título, Texto e, se houver, o Ficheiro ou link.", ""),
        ("   c. Na tabela de baixo, uma linha por elemento (um dia, uma pessoa, um vídeo...). Os nomes das colunas", ""),
        ("      mudam conforme o bloco escolhido; as colunas cinzentas não se usam nesse bloco.", ""),
        ("   d. 'Nome no menu' é o texto do botão no menu do topo. Em branco = sem botão.", ""),
        ("   e. Incluir = N esconde a secção (ou o elemento) sem apagar. Ordem: mude o número para trocar secções de lugar.", ""),
        ("   f. Quadro sem bloco escolhido é ignorado. Já vem um esqueleto típico nas primeiras secções.", ""),
        ("   g. 'Como deve ficar' (opcional) afina o desenho. No 'Bloco livre' é obrigatório: descreva o que quer ver.", ""),
        ("", ""),
        ("5. ESCREVER COM O CLAUDE", "s"),
        ("   Em cada secção há o campo 'Ideias': escreva lá o que quer dizer, em bruto (tópicos, números, notas).", ""),
        ("   Abra o Claude no Excel (painel lateral) e cole o pedido que está na folha 'Claude'. Ele escreve Pequeno título,", ""),
        ("   Título, Texto e a tabela de cada secção a partir das ideias, no tom da marca. Reveja sempre antes de publicar.", ""),
        ("", ""),
        ("6. IDIOMAS", "s"),
        ("   Escreva só em português. As colunas de inglês (lilás) são preenchidas automaticamente; se escrever lá, prevalece a sua versão.", ""),
        ("", ""),
        ("7. DRAFT E PUBLICAR", "s"),
        ("   a. Guarde o Excel e carregue em 'Gerar draft' no Studio YNG. Recebe por email o link da pré-visualização e a senha interna.", ""),
        ("   b. Veja o draft. Para corrigir: mude o Excel, guarde e carregue outra vez em 'Gerar draft'.", ""),
        ("   c. Quando o draft estiver aprovado, carregue em 'Publicar'. Sai o link final do cliente, com a senha do cliente.", ""),
        ("   d. Se mexer no Excel ou na Media depois do draft, o Publicar pede um draft novo, para nunca sair nada que não foi visto.", ""),
        ("   e. Para alterar depois de publicada: corrigir, novo draft, publicar. O link do cliente mantém-se.", ""),
        ("   Se houver erros, o Studio YNG mostra-os e recebe um email com o que corrigir.", ""),
        ("", ""),
        ("LIMITES", "s"),
        ("   Vídeos: comprimidos automaticamente para web (máx. 1080p). Nas grelhas, prefira vídeos até 2 minutos.", ""),
        ("   Imagens: JPG ou PNG. Logótipos: PNG com fundo transparente ou SVG.", ""),
        ("", ""),
        ("BLOCOS DISPONÍVEIS", "s"),
    ] + [(f"   {n}: {b['desc']}", "") for n, b in BLOCOS.items()]
    for i, (t, k) in enumerate(linhas, 1):
        c = ws.cell(i, 1, t); c.font = Font(bold=bool(k), size=14 if k == "t" else 11, color=AZUL if k else "111827")
    ws.column_dimensions["A"].width = 135

    wc = wb.create_sheet("Configuração")
    for j, h in enumerate(["Campo", "Valor", "Ajuda"], 1): _h(wc.cell(1, j, h))
    exc = exemplo.get("config", {})
    for i, (campo, ajuda, defeito) in enumerate(CONFIG, 2):
        wc.cell(i, 1, campo).font = Font(bold=True)
        v = wc.cell(i, 2, exc.get(campo, defeito) or None)
        v.fill = PatternFill("solid", fgColor=LIL if campo in AUTO else AMAR)
        wc.cell(i, 3, ajuda).font = Font(color="6B7280", italic=True)
        for j in (1, 2, 3): wc.cell(i, j).border = BORDA; wc.cell(i, j).alignment = Alignment(vertical="top", wrap_text=True)
    wc.column_dimensions["A"].width = 24; wc.column_dimensions["B"].width = 48; wc.column_dimensions["C"].width = 95
    linha = {c[0]: i for i, c in enumerate(CONFIG, 2)}
    wc.cell(linha["Cor principal"], 3).hyperlink = SELETOR_CORES
    for campo, opcoes in (("Estado", ESTADOS), ("Idiomas", IDIOMAS), ("Reprodução automática", ["S", "N"]), ("One page resumo", ["S", "N"]),
                          ("Com senha", ["S", "N"]), ("Formato", FORMATOS), ("Marca", list(MARCAS))):
        dv = DataValidation(type="list", formula1='"' + ",".join(opcoes) + '"'); wc.add_data_validation(dv); dv.add(f"B{linha[campo]}")
    wc.freeze_panes = "A2"

    # catálogo (escondido): nome | descrição | rótulos PT dos 7 slots | rótulos EN dos slots
    wbk = wb.create_sheet("_Blocos")
    for i, (n, b) in enumerate(BLOCOS.items(), 1):
        wbk.cell(i, 1, n)
        usa = ", ".join(t[0] for t in b["tab"])
        wbk.cell(i, 2, b["desc"] + (f"  Na tabela: {usa}." if usa else "  Este bloco não usa a tabela de baixo."))
        for k, t in enumerate(b["tab"][:SLOTS]):
            wbk.cell(i, 3 + k, t[0])
            if t[2]: wbk.cell(i, 3 + SLOTS + k, t[0] + " (inglês)")
    wbk.sheet_state = "hidden"

    wt = wb.create_sheet(FOLHA)
    wt.sheet_properties.tabColor = "E74F3D"
    b1 = wt.cell(1, 1, "QUANDO ACABAR: guarde o Excel e carregue em 'Gerar draft' no Studio YNG. Veja o draft e só depois carregue em 'Publicar'.")
    b1.font = Font(bold=True, size=12, color="FFFFFF"); b1.fill = PatternFill("solid", fgColor=SECC)
    wt.merge_cells(start_row=1, start_column=1, end_row=1, end_column=15)
    b2 = wt.cell(2, 1, "Abrir o Studio YNG: " + PAINEL); b2.hyperlink = PAINEL; b2.font = Font(underline="single", color="0044FF")
    larg = [18, 34, 30, 26, 24, 24, 22, 22, 22, 22, 22, 22, 22, 22, 22]
    for j, w in enumerate(larg, 1): wt.column_dimensions[get_column_letter(j)].width = w
    secs = exemplo.get("seccoes") or [{"Bloco": b, "Nome no menu": m} for b, m in ESQUELETO]
    for n in range(1, N_SECCOES + 1):
        _quadro(wt, n, secs[n - 1] if n - 1 < len(secs) else None)
    dv = DataValidation(type="list", formula1="=_Blocos!$A$1:$A$" + str(len(BLOCOS)), allow_blank=True)
    wt.add_data_validation(dv)
    for n in range(1, N_SECCOES + 1): dv.add(f"B{_r0(n)}")
    _folha_claude(wb, exemplo.get("config", {}).get("Marca") or "YoungNetwork Group")
    wb.active = wb.sheetnames.index(FOLHA)
    wb.save(saida)


# ------------------------------------------------------------------ leitura
def _v(x):
    if x is None: return ""
    if isinstance(x, float) and x.is_integer(): x = int(x)
    return str(x).strip()

def _base(nome):
    if nome in BLOCOS: return nome
    for n in BLOCOS:
        if n.lower() == (nome or "").strip().lower(): return n
    return None

def _sim(x): return (x or "S").strip().upper() not in ("N", "NÃO", "NAO", "NO", "0")

def ler(xlsx):
    """-> cfg, seccoes [{_linha, n, folha, base, incluir, ordem, menu, dur, cab, pos, itens}]"""
    wb = openpyxl.load_workbook(xlsx)   # sem data_only: as fórmulas não interessam, só os valores escritos
    cfg = {}
    for r in wb["Configuração"].iter_rows(min_row=2, values_only=True):
        if r and r[0]: cfg[_v(r[0])] = _v(r[1] if len(r) > 1 else "")
    ws = wb[FOLHA]
    secs = []
    for r in range(1, ws.max_row + 1):
        t = _v(ws.cell(r, 1).value)
        m = re.fullmatch(r"SECÇÃO (\d+)", t)
        if not m: continue
        n = int(m.group(1)); nome = _v(ws.cell(r, 2).value)
        if not nome: continue
        base = _base(nome)
        s = {"_linha": r, "n": n, "folha": f"Secção {n} ({nome})", "id": f"secao-{n}", "bloco": nome, "base": base,
             "incluir": _sim(_v(ws.cell(r, 4).value)), "ordem": _v(ws.cell(r, 9).value) or n,
             "menu": {"pt": _v(ws.cell(r, 6).value), "en": _v(ws.cell(r, 7).value)} if _v(ws.cell(r, 6).value) else None,
             "dur": _v(ws.cell(r, 11).value), "cab": {}, "pos": {"menu": (r, 7)}, "itens": []}
        for i, (rot, campo, traduz, _a) in enumerate(CAMPOS_CAB):
            rr = r + 3 + i
            pt, en = _v(ws.cell(rr, 2).value), (_v(ws.cell(rr, 3).value) if traduz else "")
            if traduz:
                s["cab"][campo] = {"pt": pt, "en": en} if pt or en else None; s["pos"][campo] = (rr, 3)
            else:
                s["cab"][campo] = pt
        rh = r + 3 + len(CAMPOS_CAB)
        tab = BLOCOS[base]["tab"] if base else []
        for i in range(N_ELEM):
            rr = rh + 1 + i
            vals = [_v(ws.cell(rr, 2 + k).value) for k in range(SLOTS)]
            if not any(vals[:len(tab)]): continue
            it = {"_linha": rr, "_incluir": _sim(_v(ws.cell(rr, 1).value)), "_pos": {}}
            for k, (rot, campo, traduz, *_x) in enumerate(tab[:SLOTS]):
                if traduz:
                    en = _v(ws.cell(rr, 2 + SLOTS + k).value)
                    it[campo] = {"pt": vals[k], "en": en} if vals[k] or en else None
                    it["_pos"][campo] = (rr, 2 + SLOTS + k)
                else:
                    it[campo] = vals[k]
            s["itens"].append(it)
        secs.append(s)
    return cfg, secs

def idiomas(cfg):
    s = (cfg.get("Idiomas") or "PT+EN").lower().replace(" ", "")
    return [l for l in s.split("+") if l in ("pt", "en", "es")] or ["pt", "en"]

def _lista(x): return [p.strip() for p in re.split(r"[;\n]", x or "") if p.strip()]

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60] or "apresentacao"

def _ativas(secs): return sorted([s for s in secs if s["incluir"]], key=lambda s: (float(s["ordem"] or 999), s["_linha"]))
def _url(x): return bool(re.match(r"https?://", x or "", re.I))
def _embed(x): return bool(re.search(r"(youtube\.com/watch|youtu\.be/|youtube\.com/shorts/|vimeo\.com/\d)", x or "", re.I))


# ------------------------------------------------------------------ traduções
def pendentes(xlsx):
    """Chaves 'Folha|linha|coluna' -> texto PT (português -> inglês, nas colunas lilás)."""
    cfg, secs = ler(xlsx)
    if "en" not in idiomas(cfg): return {}
    p = {}
    for campo in ("Título", "Barra"):
        if cfg.get(f"{campo} PT") and not cfg.get(f"{campo} EN"): p[f"cfg|{campo}|EN"] = cfg[f"{campo} PT"]
    for s in _ativas(secs):
        if s["menu"] and s["menu"]["pt"] and not s["menu"]["en"]:
            r, c = s["pos"]["menu"]; p[f"{FOLHA}|{r}|{c}"] = s["menu"]["pt"]
        for campo, (r, c) in s["pos"].items():
            v = s["cab"].get(campo)
            if campo != "menu" and v and v["pt"] and not v["en"]: p[f"{FOLHA}|{r}|{c}"] = v["pt"]
        for it in s["itens"]:
            if not it["_incluir"]: continue
            for campo, (r, c) in it["_pos"].items():
                v = it.get(campo)
                if v and v["pt"] and not v["en"]: p[f"{FOLHA}|{r}|{c}"] = v["pt"]
    return p

def escrever_traducoes(xlsx, trad):
    wb = openpyxl.load_workbook(xlsx)
    for chave, texto in trad.items():
        partes = chave.split("|")
        if partes[0] == "cfg":
            _, campo, U = partes
            ws = wb["Configuração"]; alvo = f"{campo} {U}"
            for row in ws.iter_rows(min_row=2):
                if _v(row[0].value) == alvo: row[1].value = texto
        else:
            folha, r, c = partes
            wb[folha].cell(int(r), int(c), texto)
    wb.save(xlsx)


# ------------------------------------------------------------------ validação
def validar(xlsx, media=None):
    cfg, secs = ler(xlsx)
    erros, avisos = [], []
    if not cfg.get("Título PT"): erros.append("Configuração: falta o Título PT.")
    for k in ("Cor principal", "Cor secundária"):
        if cfg.get(k) and not re.fullmatch(r"#?[0-9a-fA-F]{6}", cfg[k]):
            erros.append(f"Configuração: '{k}' tem de ser um código hexadecimal (ex.: #E30613). Seletor: {SELETOR_CORES}")
    if cfg.get("Marca") and cfg["Marca"] not in MARCAS: erros.append(f"Configuração: marca '{cfg['Marca']}' desconhecida.")
    ativas = _ativas(secs)
    if not ativas: erros.append("Conteúdo: não há nenhuma secção com bloco escolhido e Incluir = S.")
    ficheiros = set(os.listdir(media)) if media and os.path.isdir(media) else None
    def check(nome, onde):
        if not nome or _url(nome) or ficheiros is None: return
        if nome not in ficheiros:
            sem = {f.lower(): f for f in ficheiros}
            dica = f" (existe '{sem[nome.lower()]}': as maiúsculas contam)" if nome.lower() in sem else ""
            erros.append(f"{onde}: o ficheiro '{nome}' não está na pasta Media{dica}.")
    for k in ("Logo da marca", "Logo cliente"): check(cfg.get(k), f"Configuração > {k}")
    for s in ativas:
        onde = s["folha"]
        if not s["base"]: erros.append(f"{onde}: bloco desconhecido. Escolha um da lista."); continue
        b = BLOCOS[s["base"]]
        tem_cab = any((v.get("pt") if isinstance(v, dict) else v) for k, v in s["cab"].items() if k not in ("pedido", "ideias") and v)
        vivos = [i for i in s["itens"] if i["_incluir"]]
        if b["tab"] and not vivos and b["tipo"] != "livre": erros.append(f"{s['folha']}: a lista está vazia.")
        if not b["tab"] and not tem_cab: erros.append(f"{s['folha']}: está vazia.")
        if b["tipo"] == "livre" and not s["cab"].get("pedido"): erros.append(f"{s['folha']}: o Bloco livre precisa de 'Como deve ficar'.")
        if b["tipo"] == "video" and not s["cab"].get("media"): erros.append(f"{s['folha']}: falta o vídeo.")
        for f in _lista(s["cab"].get("media")): check(f, f"{s['folha']}")
        for it in vivos:
            for k in ("media", "poster"): check(it.get(k), f"{s['folha']} linha {it['_linha']}")
    return erros, avisos


# ------------------------------------------------------------------ media
def _ffprobe(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height,codec_name",
                            "-of", "json", path], capture_output=True, text=True, timeout=60)
        s = json.loads(r.stdout)["streams"][0]; return s.get("height", 0), s.get("codec_name", "")
    except Exception: return 0, ""

def _descarregar(url, pasta, avisos):
    """Links OneDrive/SharePoint e outros ficheiros diretos -> ficheiro local."""
    u = url
    if re.search(r"(1drv\.ms|sharepoint\.com|onedrive\.live\.com)", u, re.I):
        u += ("&" if "?" in u else "?") + "download=1"
    try:
        Path(pasta).mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=300) as r:
            nome = re.findall(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', r.headers.get("Content-Disposition", "") or "")
            nome = nome[0] if nome else (Path(urllib.request.urlparse(url).path).name or "ficheiro")
            nome = re.sub(r"[^\w.\-]+", "_", urllib.request.unquote(nome))
            destino = Path(pasta) / nome
            with open(destino, "wb") as f: shutil.copyfileobj(r, f)
        return destino
    except Exception as e:
        avisos.append(f"Não consegui descarregar {url}: {e}. Ponha o ficheiro na pasta Media."); return None

def preparar_media(nome, origem, destino, avisos):
    src = Path(origem) / nome
    if not src.exists(): return None
    ext = src.suffix.lower()
    base = slug(src.stem) or "media"
    if ext in (".mp4", ".mov", ".m4v", ".webm"):
        out = Path(destino) / (base + ".mp4")
        tam = src.stat().st_size / 1e6
        h, codec = _ffprobe(str(src))
        if ext == ".mp4" and codec == "h264" and h <= 1080 and tam <= 25:
            shutil.copy2(src, out)
        else:
            cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", "scale=-2:'min(1080,ih)'",
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p",
                   "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k", str(out)]
            subprocess.run(cmd, check=True, timeout=1800)
            if out.stat().st_size > 95e6:
                cmd[cmd.index("-crf") + 1] = "32"; subprocess.run(cmd, check=True, timeout=1800)
        try:
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1", "-i", str(out), "-frames:v", "1", "-vf", "scale=-2:'min(720,ih)'",
                            "-q:v", "4", str(out.with_name(out.stem + "-capa.jpg"))], check=True, timeout=120)
        except Exception: pass
        if out.stat().st_size > 95e6: avisos.append(f"{nome}: mesmo comprimido passa os 95 MB e o GitHub não aceita. Encurte o vídeo.")
        return "media/" + out.name
    if ext in (".jpg", ".jpeg", ".png", ".webp") and src.stat().st_size > 1.5e6:
        try:
            from PIL import Image
            im = Image.open(src); im.thumbnail((2200, 2200))
            out = Path(destino) / (base + (".png" if im.mode in ("RGBA", "LA", "P") else ".jpg"))
            if out.suffix == ".jpg": im.convert("RGB").save(out, quality=84, optimize=True)
            else: im.save(out, optimize=True)
            return "media/" + out.name
        except Exception: pass
    out = Path(destino) / (base + ext)
    shutil.copy2(src, out)
    return "media/" + out.name


# ------------------------------------------------------------------ briefing (para o Claude desenhar)
def _plano(v):
    if isinstance(v, dict): return {k: x for k, x in v.items() if x}
    return v

def briefing(xlsx):
    cfg, secs = ler(xlsx)
    out = []
    for s in _ativas(secs):
        b = BLOCOS.get(s["base"] or "", {})
        d = {"ficheiro": f"cena-{s['id']}.html", "classe": f"c-{s['id']}", "bloco": s["base"], "seccao": s["n"],
             "tipo": b.get("tipo"), "descricao_bloco": b.get("desc"), "menu": _plano(s["menu"])}
        for k, v in (s.get("cab") or {}).items():
            if v: d[k] = _plano(v)
        lista = []
        for it in s.get("itens") or []:
            if not it["_incluir"]: continue
            lista.append({k: _plano(v) for k, v in it.items() if not k.startswith("_") and v})
        if lista: d["lista"] = lista
        out.append(d)
    return {"config": {k: v for k, v in cfg.items() if k != "Senha" and v}, "idiomas": idiomas(cfg),
            "formato": "reel" if (cfg.get("Formato") or "").lower().startswith("r") else "pagina",
            "marca": cfg.get("Marca") or "YoungNetwork Group",
            "one_page": _sim(cfg.get("One page resumo") or "S"), "seccoes": out}


# ------------------------------------------------------------------ construção
def _txt(v, langs):
    """{'pt':..,'en':..} -> só idiomas pedidos; string simples -> igual em todos."""
    if not v: return None
    if isinstance(v, str): return {L: v for L in langs}
    d = {L: v.get(L) for L in langs if v.get(L)}
    return d or None

def _media_html(html, M, logo, logo2):
    html = html.replace("media:@logo2", logo2 or "").replace("media:@logo", logo or "")
    return re.sub(r'media:([^"\']+)', lambda m: M(m.group(1)) or m.group(0), html)

def _nova_senha():
    import secrets
    return "".join(secrets.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(8))

def garantir_senha(xlsx, campo="Senha"):
    cfg, _ = ler(xlsx)
    if campo == "Senha" and not _sim(cfg.get("Com senha") or "S"): return None
    if cfg.get(campo): return None
    nova = _nova_senha(); estado(xlsx, {campo: nova})
    return nova

def assinatura(xlsx, media=None, desenhos=None):
    """Impressão digital do conteúdo (ficha + ficheiros Media + desenhos). Muda se alguém mexer em qualquer coisa."""
    import hashlib
    cfg, secs = ler(xlsx)
    h = hashlib.sha256(json.dumps({"cfg": {k: v for k, v in cfg.items() if k not in AUTO and k not in ("Senha",)},
                                   "secs": [{k: v for k, v in s.items() if k not in ("pos",)} for s in secs]},
                                  ensure_ascii=False, sort_keys=True, default=str).encode())
    for d in (media, desenhos):
        if d and Path(d).is_dir():
            for f in sorted(Path(d).rglob("*")):
                if f.is_file() and not f.name.startswith(("~$", ".")) and f.name != "hashes.json":
                    st = f.stat(); h.update(f"{f.relative_to(d)}|{st.st_size}|{int(st.st_mtime)}".encode())
    return h.hexdigest()[:16]

def construir(xlsx, media, saida, dir_desenhos=None, modo="publicar"):
    """modo 'draft': pré-visualização interna (senha draft, faixa DRAFT). modo 'publicar': versão do cliente."""
    erros, avisos = validar(xlsx, media)
    if erros: raise SystemExit("ERROS:\n" + "\n".join(erros))
    senha_nova = garantir_senha(xlsx, "Senha draft" if modo == "draft" else "Senha")
    cfg, secs = ler(xlsx)
    if modo == "draft":
        cfg = dict(cfg); cfg["Com senha"] = "S"; cfg["Senha"] = cfg.get("Senha draft")
    langs = idiomas(cfg)
    saida = Path(saida); (saida / "media").mkdir(parents=True, exist_ok=True)
    cache = {}
    def M(nome):
        nome = (nome or "").strip()
        if not nome: return ""
        if _embed(nome): return nome
        if nome not in cache:
            if _url(nome):
                f = _descarregar(nome, saida / "_baixados", avisos)
                cache[nome] = preparar_media(f.name, f.parent, saida / "media", avisos) if f else ""
            else:
                cache[nome] = preparar_media(nome, media, saida / "media", avisos) or ""
        return cache[nome]

    marca = MARCAS.get(cfg.get("Marca") or "YoungNetwork Group", next(iter(MARCAS.values())))
    proprio = cfg.get("Logo da marca") or cfg.get("Logo YNG")
    logo = M(proprio) if proprio else ""
    lf = DIR_MARCAS / marca["pasta"] / "logo_branco.png"
    if not logo and lf.exists():
        nome = f"logo-{marca['pasta']}.png"; shutil.copy2(lf, saida / "media" / nome); logo = "media/" + nome
    logo2 = M(cfg.get("Logo cliente"))

    scenes = []
    for s in _ativas(secs):
        b = BLOCOS[s["base"]]; t = b["tipo"]; cab = s["cab"]
        meds = _lista(cab.get("media"))
        sc = {"id": s["id"], "kind": t, "menu": _txt(s["menu"], langs), "kicker": _txt(cab.get("kicker"), langs),
              "title": _txt(cab.get("title"), langs), "text": _txt(cab.get("text"), langs), "media": M(meds[0]) if meds else ""}
        for f in meds[1:]: M(f)
        sc["items"] = [{"title": _txt(it.get("title"), langs), "sub": _txt(it.get("sub"), langs), "text": _txt(it.get("text"), langs),
                        "tag": _txt(it.get("tag"), langs), "value": it.get("value") or "",
                        "goal": (_txt(it.get("goal"), langs) if isinstance(it.get("goal"), dict) else it.get("goal") or ""),
                        "media": M(it.get("media")), "poster": M(it.get("poster")),
                        "link": it.get("link") or "", "email": it.get("email") or "", "phone": it.get("phone") or ""}
                       for it in s["itens"] if it["_incluir"]]
        f = Path(dir_desenhos) / f"cena-{s['id']}.html" if dir_desenhos else None
        if f and f.exists():
            sc["html"] = _media_html(f.read_text(encoding="utf-8"), M, logo, logo2)
        elif t == "livre":
            raise SystemExit(f"ERROS:\nFolha '{s['folha']}': bloco livre por desenhar ({f.name if f else 'sem pasta de desenhos'}).")
        else:
            avisos.append(f"'{s['folha']}': sem desenho à medida, usado o desenho base do bloco.")
        try: dur = float(s["dur"] or 0) or None
        except ValueError: dur = None
        sc["dur"] = dur or {"abertura": 5, "hero": 7, "texto": 9, "numeros": 9, "cases": 4 + 1.2 * len(sc["items"]),
                            "equipa": 8, "lista": 10, "logos": 7, "contacto": 10}.get(t, 8)
        scenes.append(sc)

    titulo = _txt({"pt": cfg.get("Título PT"), "en": cfg.get("Título EN")}, langs) or {"pt": cfg.get("Título PT")}
    end = cfg.get("Endereço") or slug(cfg.get("Título PT", ""))
    meta = {"title": titulo, "kicker": _txt({"pt": cfg.get("Barra PT"), "en": cfg.get("Barra EN")}, langs), "logo": logo, "logo2": logo2,
            "autoplay": _sim(cfg.get("Reprodução automática")),
            "mode": "reel" if (cfg.get("Formato") or "Página").lower().startswith("r") else "pagina", "draft": modo == "draft"}
    cfg = dict(cfg); cfg["_marca"] = marca
    one = _sim(cfg.get("One page resumo") or "S")
    fres = Path(dir_desenhos) / "resumo.html" if dir_desenhos else None
    if one and fres and fres.exists():
        meta["resumo"] = "resumo.html"
        _pagina(saida / "resumo.html", {"meta": {**meta, "mode": "onepage"},
                "scenes": [{"id": "resumo", "kind": "texto", "html": _media_html(fres.read_text(encoding="utf-8"), M, logo, logo2)}]},
                cfg, langs, titulo, slug(end) + "-resumo")
    elif one:
        avisos.append("One page resumo pedido mas não desenhado (falta resumo.html).")
    _pagina(saida / "index.html", {"meta": meta, "scenes": scenes}, cfg, langs, titulo, slug(end))
    shutil.rmtree(saida / "_baixados", ignore_errors=True)
    return {"endereco": slug(end), "modo": modo, "assinatura": assinatura(xlsx, media, dir_desenhos),
            "seccoes": len(scenes), "one_page": bool(meta.get("resumo")), "senha_criada": senha_nova, "com_senha": _sim(cfg.get("Com senha") or "S"), "avisos": avisos, "media": len(cache)}


def _pagina(destino, data, cfg, langs, titulo, gid):
    gate = {"id": gid, "title": titulo, "langs": langs, "logo": data["meta"]["logo"], "logo2": data["meta"]["logo2"]}
    senha = cfg.get("Senha") if _sim(cfg.get("Com senha") or "S") else ""
    enc = "null"; plain = "null"
    raw = json.dumps(data, ensure_ascii=False).encode()
    if senha:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        salt, iv = os.urandom(16), os.urandom(12)
        key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=250000).derive(senha.encode())
        ct = AESGCM(key).encrypt(iv, raw, None)
        b = lambda x: base64.b64encode(x).decode()
        enc = json.dumps({"v": 1, "it": 250000, "salt": b(salt), "iv": b(iv), "ct": b(ct)})
    else:
        plain = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    mc = cfg.get("_marca") or {}
    cor1 = cfg.get("Cor principal") or mc.get("cor1") or "#E74F3D"
    cor2 = cfg.get("Cor secundária") or mc.get("cor2") or cor1
    tema = f":root{{--bg:{mc['fundo']};--bg2:{mc['fundo2']};--card:color-mix(in srgb,{mc['fundo2']} 85%,transparent)}}" if mc.get("fundo") else ""
    fix = lambda c: c if c.startswith("#") else "#" + c
    html = TEMPLATE.read_text(encoding="utf-8")
    titulo_doc = (titulo.get(langs[0]) or cfg.get("Título PT", "")).replace("<", "&lt;")
    html = (html.replace("__TITULO__", titulo_doc).replace("__TEMA__", tema).replace("__COR1__", fix(cor1)).replace("__COR2__", fix(cor2))
                .replace("__ENC__", enc).replace("__PLAIN__", plain)
                .replace("__GATE__", json.dumps(gate, ensure_ascii=False).replace("</", "<\\/")))
    Path(destino).write_text(html, encoding="utf-8")


# ------------------------------------------------------------------ estado e procura
def procurar(raiz):
    out = []
    for x in sorted(Path(raiz).glob("*/*.xlsx")):
        if x.name.startswith("~$") or x.parent.name.startswith("_"): continue
        try: cfg, _ = ler(x)
        except Exception as e: out.append({"xlsx": str(x), "erro": str(e)}); continue
        if (cfg.get("Estado") or "").strip().lower() in ("publicar", "gerar"):
            out.append({"xlsx": str(x), "pasta": str(x.parent), "pedido_por": cfg.get("Pedido por", ""), "titulo": cfg.get("Título PT", "")})
    return out

def comentario(xlsx, secao, texto):
    """Junta um comentário ao 'Como deve ficar' da secção (número ou nome no menu)."""
    _, secs = ler(xlsx)
    alvo = None
    for s in secs:
        menu = (s["menu"] or {}).get("pt") or ""
        if str(s["n"]) == str(secao).strip() or menu.strip().lower() == str(secao).strip().lower():
            alvo = s; break
    if not alvo: raise SystemExit(f"Secção '{secao}' não encontrada.")
    i = [c[1] for c in CAMPOS_CAB].index("pedido")
    wb = openpyxl.load_workbook(xlsx); ws = wb[FOLHA]
    c = ws.cell(alvo["_linha"] + 3 + i, 2)
    atual = _v(c.value)
    c.value = (atual + "\n" if atual else "") + texto
    wb.save(xlsx)
    return {"secao": alvo["n"], "bloco": alvo["bloco"], "como_deve_ficar": c.value}

def estado(xlsx, valores):
    wb = openpyxl.load_workbook(xlsx); ws = wb["Configuração"]
    for r in ws.iter_rows(min_row=2):
        k = _v(r[0].value)
        if k in valores: r[1].value = valores[k]
    wb.save(xlsx)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("modelo"); a.add_argument("saida"); a.add_argument("--exemplo")
    a = sp.add_parser("validar"); a.add_argument("xlsx"); a.add_argument("--media")
    a = sp.add_parser("pendentes"); a.add_argument("xlsx")
    a = sp.add_parser("traduzir"); a.add_argument("xlsx"); a.add_argument("trad")
    a = sp.add_parser("briefing"); a.add_argument("xlsx")
    a = sp.add_parser("procurar"); a.add_argument("raiz")
    a = sp.add_parser("estado"); a.add_argument("xlsx"); a.add_argument("pares", nargs="+", help='"Campo=valor"')
    a = sp.add_parser("comentario"); a.add_argument("xlsx"); a.add_argument("secao"); a.add_argument("texto")
    a = sp.add_parser("construir"); a.add_argument("xlsx"); a.add_argument("--media", required=True); a.add_argument("--saida", required=True)
    a.add_argument("--desenhos", help="pasta com cena-secao-<n>.html (e resumo.html) desenhados à medida")
    a.add_argument("--modo", choices=["draft", "publicar"], default="publicar")
    a = sp.add_parser("assinatura"); a.add_argument("xlsx"); a.add_argument("--media"); a.add_argument("--desenhos")
    x = ap.parse_args()
    j = lambda o: print(json.dumps(o, ensure_ascii=False, indent=1))
    if x.cmd == "modelo": criar_modelo(x.saida, json.load(open(x.exemplo, encoding="utf-8")) if x.exemplo else None)
    elif x.cmd == "validar":
        e, w = validar(x.xlsx, x.media); j({"erros": e, "avisos": w}); sys.exit(1 if e else 0)
    elif x.cmd == "pendentes": j(pendentes(x.xlsx))
    elif x.cmd == "traduzir": escrever_traducoes(x.xlsx, json.load(open(x.trad, encoding="utf-8")))
    elif x.cmd == "briefing": j(briefing(x.xlsx))
    elif x.cmd == "procurar": j(procurar(x.raiz))
    elif x.cmd == "estado": estado(x.xlsx, dict(p.split("=", 1) for p in x.pares))
    elif x.cmd == "comentario": j(comentario(x.xlsx, x.secao, x.texto))
    elif x.cmd == "construir": j(construir(x.xlsx, x.media, x.saida, x.desenhos, x.modo))
    elif x.cmd == "assinatura": print(assinatura(x.xlsx, x.media, x.desenhos))

if __name__ == "__main__":
    main()
