#!/usr/bin/env python3
"""Abre uma apresentação gerada num browser sem ecrã e tira capturas (desktop e telemóvel, todos os idiomas).
Uso: testar.py PASTA_SITE ENDERECO SAIDA_CAPTURAS [--senha X]"""
import argparse, http.server, threading, functools, os, sys, json
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("site"); ap.add_argument("endereco"); ap.add_argument("saida"); ap.add_argument("--senha", default="")
ap.add_argument("--langs", default="pt,en")
a = ap.parse_args()
os.makedirs(a.saida, exist_ok=True)
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=a.site)
http.server.SimpleHTTPRequestHandler.log_message = lambda *x: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}/{a.endereco}/"
erros = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for nome, vp in (("desk", {"width": 1366, "height": 768}), ("mob", {"width": 375, "height": 812})):
        for pag in ("index.html", "resumo.html"):
            if not os.path.exists(os.path.join(a.site, a.endereco, pag)): continue
            for L in a.langs.split(","):
                ctx = b.new_context(viewport=vp, device_scale_factor=1)
                ctx.add_init_script(f"localStorage.setItem('yng-lang','{L}')")
                pg = ctx.new_page()
                pg.on("pageerror", lambda e: erros.append(f"{nome}/{pag}/{L}: {e}"))
                pg.goto(base + pag)
                if a.senha:
                    pg.wait_for_selector("#gPass", state="visible")
                    pg.fill("#gPass", a.senha); pg.click("#gForm button")
                pg.wait_for_selector("#app:not([hidden])", timeout=15000)
                pg.wait_for_timeout(1200)
                # forçar todas as secções visíveis para a captura de página inteira
                pg.evaluate("document.querySelectorAll('.scene').forEach(s=>{s.classList.add('in');s.querySelectorAll('.tr i[data-w]').forEach(i=>i.style.width=i.dataset.w+'%')})")
                pg.wait_for_timeout(900)
                larg = pg.evaluate("document.documentElement.scrollWidth > innerWidth")
                if larg: erros.append(f"{nome}/{pag}/{L}: scroll horizontal")
                pg.screenshot(path=f"{a.saida}/{pag.split('.')[0]}-{nome}-{L}.png", full_page=True)
                ctx.close()
    b.close()
print(json.dumps({"erros": erros}, ensure_ascii=False, indent=1))
