"""Etapa 3 - Cruza a rede LinkedIn com os participantes da agenda.

Entradas: dados/agenda.json (etapa 1), dados/rede_linkedin.json (etapa 2)
          config/revisao_manual.csv (opcional; colunas: chave_linkedin;status)
Saída   : dados/cruzamento.json

Regra de correspondência
  - nomes normalizados (sem acentos, partículas e sufixos);
  - primeiro nome igual e último sobrenome do LinkedIn presente no nome da agenda;
  - se o nome do LinkedIn tiver sobrenomes do meio, ao menos um deles precisa constar na agenda.
Confiança
  - Confirmado : nome idêntico, ou nome com 3+ termos todos presentes, ou coincidência
                 entre a instituição da agenda e o título do LinkedIn;
  - Provável   : todos os termos presentes e título com perfil acadêmico/profissional compatível;
  - A verificar: demais coincidências de nome (nomes comuns, vínculos distintos);
  - Descartado : primeiro nome muito comum e sem nenhum indício adicional.
A revisão manual (CSV) sempre prevalece: status aceitos = Confirmado, Provável, A verificar, Descartado.
"""
import csv
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from comum import RAIZ, carregar_config, chave_nome, gravar_json, ler_json, sem_acento, tokens_nome  # noqa: E402

GENERICAS = {"programa", "pos", "graduacao", "administracao", "universidade", "federal", "estado",
             "mestrado", "doutorado", "prog", "grad", "admin", "escola", "departamento", "centro",
             "instituto", "sem", "vinculado", "curso", "profissional", "publica", "gestao", "the",
             "and", "em", "area", "campus", "faculdade", "ciencias", "nacional", "dos", "rio", "sao"}
RE_PROF = re.compile(r"profess|pesquis|doutor|phd|mestr|research|univers|docente|lecturer|scholar|"
                     r"servidor|analista|auditor|especialista|coordenador|diretor", re.I)


def palavras(s):
    return set(re.findall(r"[a-z]{3,}", sem_acento(s))) - GENERICAS


def main():
    cfg = carregar_config()
    agenda = ler_json("agenda.json")
    if not os.path.exists(os.path.join(RAIZ, "dados", "rede_linkedin.json")):
        print("[aviso] dados/rede_linkedin.json ausente: painel será gerado só com potenciais contatos")
        gravar_json([], "cruzamento.json")
        return
    rede = ler_json("rede_linkedin.json")
    eu = chave_nome(cfg.get("pesquisador", {}).get("nome_na_agenda", ""))

    # pessoas da rede, sem duplicidade (a mesma pessoa pode ser conexão e seguidora)
    pessoas = {}
    for lista, rotulo in (("conexoes", "Conexão"), ("seguidores", "Seguidor"), ("seguindo", "Seguindo")):
        for p in rede.get(lista, []):
            nome = re.sub(r",.*$", "", p["nome"]).strip(" '\"")
            k = chave_nome(nome)
            if len(k.split()) < 2:
                continue
            e = pessoas.setdefault(k, {"nome": nome, "titulo": p.get("titulo", ""), "url": p.get("url", ""), "vinculos": set()})
            e["vinculos"].add(rotulo)
            if len(p.get("titulo", "")) > len(e["titulo"]):
                e["titulo"] = p["titulo"]
            if lista == "conexoes":
                e["url"] = p.get("url", e["url"])

    por_chave = defaultdict(list)
    for r in agenda:
        k = chave_nome(r["nome"])
        if len(k.split()) >= 2 and k != eu:
            por_chave[k].append(r)
    por_primeiro = defaultdict(list)
    for k in por_chave:
        por_primeiro[k.split()[0]].append(k)
    freq_primeiro = Counter(k.split()[0] for k in por_chave)

    revisao = {}
    caminho = os.path.join(RAIZ, "config", "revisao_manual.csv")
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            for linha in csv.DictReader(f, delimiter=";"):
                revisao[(linha["chave_linkedin"].strip(), linha.get("chave_agenda", "").strip())] = linha["status"].strip()

    saida = []
    for k, e in pessoas.items():
        t = k.split()
        for ak in por_primeiro.get(t[0], []):
            at = ak.split()
            resto = set(at[1:])
            if t[-1] not in resto:
                continue
            meio = t[1:-1]
            faltam = [x for x in meio if x not in resto]
            if meio and len(faltam) == len(meio):
                continue
            afil = " ".join(r["afiliacao"] for r in por_chave[ak])
            comum_inst = sorted(palavras(afil) & palavras(e["titulo"]))
            identico = t == at
            todos = not faltam
            if identico or (todos and len(t) >= 3) or (todos and comum_inst):
                status = "Confirmado"
                if not identico and not comum_inst and len(t) == 2:
                    status = "Provável"
            elif todos and RE_PROF.search(e["titulo"] or "") and freq_primeiro[t[0]] < 25:
                status = "Provável"
            elif todos:
                status = "A verificar"
            else:
                status = "Descartado"
            status = revisao.get((k, ak), revisao.get((k, ""), status))
            saida.append(dict(chave_linkedin=k, chave_agenda=ak, status=status, nome_linkedin=e["nome"],
                              titulo=e["titulo"], url=e["url"], vinculos=sorted(e["vinculos"]),
                              instituicao_em_comum=comum_inst))
    gravar_json(saida, "cruzamento.json")
    print(Counter(x["status"] for x in saida))
    print("Revise os casos 'Provável' e 'A verificar' e registre decisões em config/revisao_manual.csv")


if __name__ == "__main__":
    main()
