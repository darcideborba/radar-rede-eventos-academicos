"""Funções compartilhadas pelos scripts do pipeline."""
import json
import os
import re
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "dados")

PARTICULAS = {"de", "da", "do", "dos", "das", "e", "di", "del", "y", "van", "von",
              "junior", "jr", "filho", "neto", "prof", "dr", "dra", "phd", "msc", "me", "ms"}


def carregar_config(caminho=None):
    caminho = caminho or os.path.join(RAIZ, "config", "config.json")
    if not os.path.exists(caminho):
        caminho = os.path.join(RAIZ, "config", "config.exemplo.json")
        print(f"[aviso] config/config.json não encontrado; usando {caminho}")
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def sem_acento(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def tokens_nome(s):
    """Nome normalizado: sem acentos, sem pontuação, sem partículas e sufixos."""
    s = sem_acento(s)
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z ]", " ", s)
    return [t for t in s.split() if t not in PARTICULAS and len(t) > 1]


def chave_nome(s):
    return " ".join(tokens_nome(s))


def chave_data(d, t=""):
    """dd/mm/aaaa -> aaaammdd para ordenação."""
    d = d or "99/99/9999"
    return d[6:] + d[3:5] + d[:2] + (t or "")


def ler_json(nome):
    with open(os.path.join(DADOS, nome), encoding="utf-8") as f:
        return json.load(f)


def gravar_json(obj, nome):
    os.makedirs(DADOS, exist_ok=True)
    with open(os.path.join(DADOS, nome), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    print(f"[ok] dados/{nome}")


def instituicao_curta(afil):
    """Extrai a instituição principal de 'Programa / Instituição) - (Outro'."""
    afil = re.sub(r"\s+", " ", afil or "")
    primeira = re.split(r"\)\s*-\s*\(", afil)[0]
    return (primeira.split(" / ")[-1] if " / " in primeira else primeira)[:70]


def instituicoes(afiliacoes, aliases=None):
    """Lista de instituições (siglas quando houver) a partir de todas as afiliações de uma pessoa.

    `aliases` (config: evento.aliases_instituicoes) unifica grafias: {"variante": "canônica"};
    use null como valor para descartar rótulos que não são instituições.
    """
    aliases = aliases or {}
    saida = set()
    for afil in afiliacoes:
        for seg in re.split(r"\)\s*-\s*\(", afil or ""):
            seg = seg.strip(" ()")
            if " / " in seg:
                seg = seg.split(" / ")[-1].strip(" ()")
            if not seg or seg.upper() in ("NA", "N/A", "OUTRO", "OUTRA"):
                continue
            partes = [x.strip() for x in re.split(r"\s[-–]\s", seg)]
            siglas = [x for x in partes if re.fullmatch(r"[A-ZÀ-Ý0-9\-/]{2,12}", x.replace(" ", ""))]
            rotulo = re.sub(r"\s+", " ", siglas[0] if siglas else partes[0])[:60]
            rotulo = aliases.get(rotulo, rotulo)
            if rotulo == "_nota":
                continue
            if rotulo and len(rotulo) >= 3:
                saida.add(rotulo)
    return sorted(saida)
