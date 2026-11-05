"""Roda todos os testes com cobertura e grava as evidências em docs/testes/.

Uso (na pasta do projeto, com o ambiente virtual ativo):
    pip install -r requirements-dev.txt
    python -m tests.gerar_relatorio

Gera:
    docs/testes/RELATORIO_TESTES.md   resumo legível (totais, tempo por teste, cobertura por módulo, desempenho)
    docs/testes/execucao.txt          saída completa do pytest (evidência bruta)
    docs/testes/junit.xml             resultado em formato JUnit (lido por ferramentas de CI)
    docs/testes/cobertura/index.html  relatório de cobertura linha a linha
"""
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

OUT = Path("docs/testes")
TIPO = {"test_unidades": "Unitário", "test_smoke": "Componente", "test_api": "Ponta a ponta (API)",
        "test_cenario_jose": "Aceite / desempenho"}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="vintmatch_cov_"))
    # COVERAGE_FILE fora do projeto: não deixa arquivos .coverage na pasta; UTF-8 para o Windows não trocar acentos
    env = dict(os.environ, COVERAGE_FILE=str(tmp / ".coverage"), PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    cmd = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-W", "ignore::DeprecationWarning", "-v", "-s",
           "--durations=10", "--cov=app", "--cov-report=term-missing", f"--cov-report=html:{OUT / 'cobertura'}",
           f"--cov-report=json:{tmp / 'cov.json'}", f"--junitxml={OUT / 'junit.xml'}"]
    inicio = datetime.now()
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8", errors="replace")
    duracao = time.time() - t0
    (OUT / "execucao.txt").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    # o coverage.py cria um .gitignore com "*" na pasta do HTML; aqui o relatório deve ir para o repositório
    (OUT / "cobertura" / ".gitignore").write_text("# relatório de cobertura versionado de propósito (evidência)\n",
                                                  encoding="utf-8")

    casos = []
    for tc in ET.parse(OUT / "junit.xml").getroot().iter("testcase"):
        arq = tc.get("classname", "").split(".")[-1]
        st = "Falhou" if tc.find("failure") is not None or tc.find("error") is not None else \
             "Ignorado" if tc.find("skipped") is not None else "Passou"
        casos.append({"arq": arq, "nome": tc.get("name"), "tempo": float(tc.get("time") or 0), "status": st})
    cov = json.loads((tmp / "cov.json").read_text(encoding="utf-8"))
    perf = re.search(r"mediana (\d+) ms, máx (\d+) ms \((\d+) colaboradores, (\d+) talentos\)", proc.stdout)

    total, ok = len(casos), sum(c["status"] == "Passou" for c in casos)
    por_tipo = {}
    for c in casos:
        t = TIPO.get(c["arq"], c["arq"])
        por_tipo.setdefault(t, [0, 0, 0.0])
        por_tipo[t][0] += 1
        por_tipo[t][1] += c["status"] == "Passou"
        por_tipo[t][2] += c["tempo"]

    L = [f"# Relatório de testes automatizados — VINT Match", "",
         f"Executado em {inicio:%d/%m/%Y %H:%M} · Python {platform.python_version()} · {platform.system()} · "
         f"duração total {duracao:.1f} s", "",
         f"**Resultado: {ok} de {total} testes passaram"
         f"{'' if ok == total else f' — {total - ok} com falha'}. "
         f"Cobertura de código do pacote `app`: {cov['totals']['percent_covered']:.0f}%.**", "",
         "## Por tipo de teste", "", "| Tipo | Testes | Passaram | Tempo (s) |", "| --- | --- | --- | --- |"]
    for t, (n, p, s) in por_tipo.items():
        L.append(f"| {t} | {n} | {p} | {s:.2f} |")
    if perf:
        L += ["", "## Desempenho do cruzamento das bases", "",
              f"Cenário do José (Node.js + AWS, Sênior, 50%, 3 meses), 20 execuções: mediana **{perf[1]} ms**, "
              f"máximo **{perf[2]} ms**, cruzando {perf[3]} colaboradores do SGD e {perf[4]} talentos do iHiring."]
    L += ["", "## Cobertura por módulo", "", "| Módulo | Linhas | Não cobertas | Cobertura |", "| --- | --- | --- | --- |"]
    for nome, f in sorted(cov["files"].items()):
        s = f["summary"]
        L.append(f"| `{nome.replace(os.sep, '/')}` | {s['num_statements']} | {s['missing_lines']} | {s['percent_covered']:.0f}% |")
    t = cov["totals"]
    L.append(f"| **Total** | {t['num_statements']} | {t['missing_lines']} | **{t['percent_covered']:.0f}%** |")
    L += ["", "## Todos os testes", "", "| Arquivo | Teste | Tipo | Tempo (s) | Resultado |", "| --- | --- | --- | --- | --- |"]
    for c in casos:
        L.append(f"| `{c['arq']}.py` | `{c['nome']}` | {TIPO.get(c['arq'], '')} | {c['tempo']:.2f} | {c['status']} |")
    L += ["", "Evidências: `execucao.txt` (saída completa), `junit.xml`, `cobertura/index.html` (linha a linha).", ""]
    (OUT / "RELATORIO_TESTES.md").write_text("\n".join(L), encoding="utf-8")
    print(f"{ok}/{total} testes passaram · cobertura {cov['totals']['percent_covered']:.0f}% · relatório em {OUT / 'RELATORIO_TESTES.md'}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
