#!/usr/bin/env bash
# Executa o pipeline completo (etapas 1, 3, 4 e 5). A etapa 2 é manual, no navegador.
set -e
cd "$(dirname "$0")"
python3 scripts/01_extrair_agenda.py
python3 scripts/03_cruzar_rede.py
python3 scripts/04_pontuar_potenciais.py
python3 scripts/05_gerar_painel_e_planilha.py
echo "Pronto: abra saida/painel.html no navegador."
