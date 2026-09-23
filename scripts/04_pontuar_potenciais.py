"""Etapa 4 - Pontua os participantes que NÃO estão na rede (potenciais contatos).

Entradas: dados/agenda.json, dados/cruzamento.json, config (aderencia, pesos, cortes)
          config/perfis_localizados.json (opcional: {"Nome na agenda": "https://linkedin.com/in/..."})
Saída   : dados/potenciais.json

Pontuação (todos os pesos vêm do config):
  sessão núcleo (6) + sessão adjacente (2) + 1,5 por título aderente (máx. 3)
  + peso do papel (palestrante 5 ... autor 1) + afiliação prioritária (3)
  + bônus por divisão + 20 se estiver na mesma sessão do pesquisador.
Prioridade: A >= corte A (ou mesma sessão); B >= corte B; C >= mínimo para listar.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from comum import RAIZ, carregar_config, chave_nome, gravar_json, ler_json, sem_acento  # noqa: E402


def rx(lista):
    return re.compile("|".join(lista)) if lista else re.compile(r"(?!x)x")


def sessoes_do_pesquisador(agenda, eu):
    return {(r["data"], r["hora"], r["sala"]) for r in agenda if eu and chave_nome(r["nome"]) == eu}


def main():
    cfg = carregar_config()
    ad, pesos, cortes = cfg["aderencia"], cfg["pesos"], cfg["cortes"]
    agenda = ler_json("agenda.json")
    eu = chave_nome(cfg.get("pesquisador", {}).get("nome_na_agenda", ""))
    minhas = sessoes_do_pesquisador(agenda, eu)
    na_rede = set()
    if os.path.exists(os.path.join(RAIZ, "dados", "cruzamento.json")):
        na_rede = {c["chave_agenda"] for c in ler_json("cruzamento.json") if c["status"] in ("Confirmado", "Provável")}
    perfis = {}
    caminho = os.path.join(RAIZ, "config", "perfis_localizados.json")
    if os.path.exists(caminho):
        perfis = json.load(open(caminho, encoding="utf-8"))

    NUC, ADJ, TIT, AFI = rx(ad["sessoes_nucleo"]), rx(ad["sessoes_adjacentes"]), rx(ad["titulos_trabalhos"]), rx(ad["afiliacoes_prioritarias"])
    TEMAS = {k: re.compile(v) for k, v in ad.get("temas_rotulos", {}).items()}

    grupos = {}
    for r in agenda:
        k = chave_nome(r["nome"])
        if len(k.split()) < 2 or k == eu:
            continue
        g = grupos.setdefault(k, {"nome": r["nome"], "afiliacoes": set(), "papeis": set(), "itens": []})
        if r["afiliacao"]:
            g["afiliacoes"].add(r["afiliacao"])
        g["papeis"].add(r["papel"])
        g["itens"].append(r)

    saida = []
    for k, g in grupos.items():
        if k in na_rede:
            continue
        nucleo = any(NUC.search(sem_acento(r["sessao"])) for r in g["itens"])
        adj = (not nucleo) and any(ADJ.search(sem_acento(r["sessao"])) for r in g["itens"])
        titulos = sum(1 for r in g["itens"] if r["titulo"] and TIT.search(sem_acento(r["titulo"])))
        afil = " | ".join(sorted(g["afiliacoes"]))
        gov = bool(AFI.search(sem_acento(afil)))
        mesma = any((r["data"], r["hora"], r["sala"]) in minhas for r in g["itens"])
        papel = max(pesos["papel"].get(p, 1) for p in g["papeis"])
        bonus_div = max([pesos.get("divisao_bonus", {}).get(r["divisao"], 0) for r in g["itens"]] + [0])
        nota = (pesos["sessao_nucleo"] * nucleo + pesos["sessao_adjacente"] * adj
                + pesos["titulo_aderente"] * min(titulos, pesos["max_titulos"]) + papel
                + pesos["afiliacao_prioritaria"] * gov + bonus_div + pesos["mesma_sessao_do_pesquisador"] * mesma)
        if nota < cortes["minimo_para_listar"] and not mesma:
            continue
        prioridade = "A" if (nota >= cortes["prioridade_A"] or mesma) else ("B" if nota >= cortes["prioridade_B"] else "C")
        texto = sem_acento(" ".join((r["sessao"] or "") + " " + (r["titulo"] or "") for r in g["itens"]))
        nome = g["nome"].title() if g["nome"].isupper() else g["nome"]
        saida.append(dict(chave=k, nome=nome, prioridade=prioridade, pontuacao=round(nota, 1),
                          mesma_sessao=mesma, afiliacao_prioritaria=gov, afiliacao=afil,
                          papeis=sorted(g["papeis"]), temas=[t for t, r in TEMAS.items() if r.search(texto)],
                          url=perfis.get(g["nome"]) or perfis.get(nome, ""), itens=g["itens"]))
    saida.sort(key=lambda x: ("ABC".index(x["prioridade"]), -x["pontuacao"]))
    gravar_json(saida, "potenciais.json")
    from collections import Counter
    print(len(saida), "potenciais contatos", Counter(x["prioridade"] for x in saida))


if __name__ == "__main__":
    main()
