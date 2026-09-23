"""Etapa 1 - Extrai as participações da Programação Detalhada (PDFs por divisão).

Entrada : <pasta_agenda>/Programacao-detalhada-<divisao>.pdf  (config.evento.pasta_agenda)
Saída   : dados/agenda.json  (uma linha por participação: pessoa x sessão)

Requer o utilitário `pdftotext` (poppler-utils). O parser foi escrito para o
layout da ANPAD (EnANPAD); para outro evento, ajuste as expressões regulares
de papel (PAPEIS), código de trabalho (RE_CODIGO) e horário (RE_HORA).
"""
import glob
import os
import re
import subprocess
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from comum import RAIZ, carregar_config, gravar_json  # noqa: E402

PAPEIS = {
    "Coordenador/Debatedor": "Coordenador/Debatedor", "Coordenador": "Coordenador",
    "Coordenadora": "Coordenador", "Coordenação": "Coordenador", "Debatedor": "Debatedor",
    "Debatedora": "Debatedor", "Painelistas": "Painelista", "Painelistas convidados SEBRAE": "Painelista",
    "Proponente": "Proponente", "Editor": "Editor", "Editores/Organizadores": "Editor",
    "Palestrante": "Palestrante", "Palestrantes": "Palestrante", "Mentor": "Mentor",
    "Mentorado": "Mentorado", "Mentorados": "Mentorado", "Organizadores": "Organizador",
    "Participantes com trabalhos aceitos": "Autor", "Participantes com trabalho aprovado": "Autor",
    "Autores com trabalhos aceitos": "Autor", "Aprovados para discussão": "Autor (PDW)",
    "Participantes": "Participante", "Moderador": "Moderador", "Moderadora": "Moderador",
    "Mediador": "Moderador", "Mediadora": "Moderador", "Ministrantes": "Ministrante",
    "Facilitador": "Facilitador", "Diretoria da ANPAD": "Diretoria ANPAD",
    "Coordenador do EnANPAD Profissional": "Coordenador",
}
RE_CODIGO = re.compile(r"^([A-Z]{2,4}\d{3,6})\b(.*)$")
RE_HORA = re.compile(r"^(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})\s*-\s*(.*)$")
RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
PARTE = r"[A-ZÀ-Ýa-zà-ÿ][A-Za-zÀ-ÿ'`´\.\-]*"
RE_NOME_PAR = re.compile(r"^(" + PARTE + r"(?: " + PARTE + r"){1,8})\s*\((.*)\)\s*$", re.S)
RE_NOME_HIFEN = re.compile(r"^(?:Prof\.?(?:ª|a)?\.? (?:Dr\.?(?:ª|a)?\.? )?)?(" + PARTE + r"(?: " + PARTE + r"){1,8})\s*[-–]\s*(.+)$")
RE_NOME_SO = re.compile(r"^(" + PARTE + r"(?: " + PARTE + r"){1,7})$")
MINUSC = {"de", "da", "do", "dos", "das", "e", "di", "del", "van", "von", "y"}
CABECALHOS = ("L Encontro da ANPAD", "UNIFOR, Fortaleza")


def parece_nome(s):
    t = s.split()
    if not (2 <= len(t) <= 9) or any(c.isdigit() for c in s):
        return False
    return all(x[0].isupper() or x.lower() in MINUSC for x in t)


def paragrafos(linhas):
    """Agrupa linhas em parágrafos, quebrando em cabeçalhos estruturais e nomes."""
    paras, cur = [], []

    def fecha():
        if cur:
            paras.append(" ".join(cur))
            cur.clear()

    for l in linhas:
        l = l.replace("\f", "").strip()
        if not l or l.startswith(CABECALHOS) or re.fullmatch(r"\d+", l):
            fecha()
            continue
        cauda = re.search(r"\)\s+([A-Z]{2,4}\d{3,6}(?:\s+Tema.*)?)$", l)
        if cauda:  # código de trabalho colado ao fim da linha do autor anterior
            cur.append(l[:cauda.start(1)].strip())
            fecha()
            paras.append(cauda.group(1))
            continue
        if l.startswith("•"):
            fecha()
            cur.append(l.lstrip("• ").strip())
            continue
        estrutural = (RE_CODIGO.match(l) or RE_HORA.match(l) or RE_DATA.match(l)
                      or (l.endswith(":") and l.rstrip(":") in PAPEIS) or l in PAPEIS
                      or l.startswith("Idioma da sessão") or l.startswith("Apresentação de Trabalho"))
        if estrutural:
            fecha()
            paras.append(l)
            continue
        if cur:
            atual = " ".join(cur)
            if RE_NOME_PAR.match(atual) or (RE_NOME_HIFEN.match(atual) and not cur[-1].endswith("-")):
                m = RE_NOME_HIFEN.match(l)
                if ("(" in l and RE_NOME_PAR.match(l.split(" (")[0] + " (x)")) \
                        or (m and parece_nome(m.group(1))) or (RE_NOME_SO.match(l) and parece_nome(l)):
                    fecha()
        cur.append(l)
    fecha()
    return paras


def extrair_arquivo(txt, divisao):
    linhas = open(txt, encoding="utf-8").read().splitlines()
    linhas_saida = []
    data = hora = sala = tipo = sessao = papel = codigo = titulo = esperado = None
    for p in paragrafos(linhas):
        if RE_DATA.match(p):
            data = p
            continue
        m = RE_HORA.match(p)
        if m:
            hora, sala = m.group(1), m.group(2)
            sessao = tipo = papel = codigo = titulo = None
            esperado = "tipo"
            continue
        k = p.rstrip(":")
        if k in PAPEIS and (p.endswith(":") or p in PAPEIS):
            papel, codigo, titulo = PAPEIS[k], None, None
            continue
        if p.startswith("Idioma da sessão"):
            esperado = "sessao"
            continue
        m = RE_CODIGO.match(p)
        if m and ("Tema" in p or len(p) <= 12):
            codigo, papel, esperado = m.group(1), "Autor", "titulo"
            continue
        if esperado == "tipo":
            if p.startswith("Apresentação"):
                tipo, esperado = p, "sessao"
            else:
                tipo, sessao, esperado = "Sessão especial", p, None
            continue
        if esperado == "sessao":
            sessao, esperado = p, None
            continue
        if esperado == "titulo":
            titulo, esperado = p, None
            continue
        candidatos = []
        m = RE_NOME_PAR.match(p)
        if m:
            candidatos = [(m.group(1), m.group(2))]
        elif p.startswith("Convidado(a)/palestrante:"):
            mm = RE_NOME_HIFEN.match(p.split(":", 1)[1].strip())
            if mm:
                candidatos, papel = [(mm.group(1), mm.group(2))], "Palestrante"
        elif papel == "Autor (PDW)" and " - " in p:
            candidatos = [(n.strip(), "") for n in p.rsplit(" - ", 1)[1].split(";")]
        else:
            m = RE_NOME_HIFEN.match(p)
            if m and papel and parece_nome(m.group(1)):
                candidatos = [(m.group(1), m.group(2))]
            elif papel and RE_NOME_SO.match(p) and parece_nome(p):
                candidatos = [(p, "")]
            elif papel and re.match(r"^(.+?) \((.+)\)$", p):
                mm = re.match(r"^(.+?) \((.+)\)$", p)
                candidatos = [(mm.group(1), mm.group(2))]
        for nome, afil in candidatos:
            nome = nome.strip()
            if not parece_nome(nome) and papel != "Autor (PDW)":
                continue
            linhas_saida.append(dict(divisao=divisao, data=data, hora=hora, sala=sala, tipo=tipo,
                                     sessao=sessao, papel=papel or "Participante", nome=nome,
                                     afiliacao=afil.strip(), codigo=codigo, titulo=titulo))
    return linhas_saida


def main():
    cfg = carregar_config()
    pasta = os.path.join(RAIZ, cfg["evento"]["pasta_agenda"])
    pdfs = sorted(glob.glob(os.path.join(pasta, "*.pdf")))
    if not pdfs:
        sys.exit(f"Nenhum PDF em {pasta}")
    tmp = os.path.join(RAIZ, "dados", "_txt")
    os.makedirs(tmp, exist_ok=True)
    todas = []
    for pdf in pdfs:
        base = os.path.splitext(os.path.basename(pdf))[0]
        divisao = base.split("detalhada-")[-1].upper()
        txt = os.path.join(tmp, base + ".txt")
        subprocess.run(["pdftotext", "-layout", pdf, txt], check=True)
        todas += extrair_arquivo(txt, divisao)
    todas = [r for r in todas if r["data"]]
    gravar_json(todas, "agenda.json")
    print(f"{len(todas)} participações | {len({r['nome'].lower() for r in todas})} nomes únicos")
    print(Counter(r["papel"] for r in todas).most_common())


if __name__ == "__main__":
    main()
