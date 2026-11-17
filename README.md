# Material suplementar – ReDoS: retrocesso, autômatos finitos e expressões reais

Ambiente: Linux (VM), Intel Xeon 2,1 GHz, Python 3.13.18. Tempos absolutos dependem do equipamento.

## Experimentos controlados
- `exp.py`: analisador de expressões, construção de Thompson, simulação do AFN, construção de subconjuntos (AFD) e retrocesso do módulo `re` (funções reutilizadas pelos demais scripts).
- `exp6.py` (versão final): igual ao `exp4.py`, mas guarda as 5 execuções individuais (`raw`), média, desvio-padrão, mediana e faixa. Saídas: `results6.json` (tempos) e `results7.json` (família L_k). As tabelas e figuras do artigo usam média e desvio-padrão dessa rodada.
- `exp4.py`: rodada anterior (mediana e faixa, sem execuções individuais); varredura completa com 5 execuções por configuração (mediana, mínimo, máximo), limite de 3 s por execução do retrocesso, aquecimento prévio, e família L_k (k = 2..14). Saídas: `results4.json`, `results5.json`.
- `exp3.py`: comparação em Python puro (retrocesso sobre o AFN, sem memorização, x simulação do AFN). Saída: `results3.json` (seção B). A seção A é um teste anterior de repetições.
- `results_re2.json`: tempos do RE2 (pacote `google-re2`) em P1–P4 e C1 com n = 26, 10.000 e 1.000.000 (mediana de 5 execuções).
- `exp2.py`: versão original (uma medida) da família L_k.

## Expressões reais
- `extract.py`: extrai, pela árvore sintática (ast), literais de padrão passados a compile/match/search/fullmatch/findall/finditer/sub/subn/split do módulo `re`, na biblioteca padrão e em 17 pacotes. Exclui diretórios cujo caminho contém "test"; duplicatas = texto do padrão idêntico.
- `analyze.py`: critério estático (repetição aninhada, alternância sob repetição, lookaround, referência a grupo), teste dinâmico (exponencial: n = 16, 22, 28, limite 1 s; polinomial: n = 2.000 e 8.000, limite 2 s) e compatibilidade com RE2.
- `confirm.py`: reexecução dos 24 casos quadráticos (n = 1.000..8.000 com search e match; RE2 com n = 8.000, 100.000, 1.000.000).
- `corpus_analise.csv` / `analise_completa.json`: as 714 expressões com fontes e classificação. `casos_quadraticos.json`: tempos individuais dos 24 casos.

Versões analisadas (nº de expressões): Pygments 2.21.0 (201), docutils 0.23 (61), Markdown 3.11.3 (45), Babel 2.18.0 (38), Tornado 6.6.1 (36), packaging 26.3 (34), bleach 6.4.0 (26), Werkzeug 3.1.9 (23), Jinja2 3.1.6 (16), urllib3 2.8.0 (12), sqlparse 0.6.1 (11), httpx 0.28.1 (11), PyYAML 6.0.3 (10), requests 2.34.2 (8), Click 8.5.1 (3), idna 3.20 (2), Flask 3.1.3 (1); biblioteca padrão do Python 3.13.18 (202). A soma (740) excede 714 porque 26 expressões ocorrem em mais de uma fonte.

## Licenças
As expressões foram extraídas de pacotes de código aberto e permanecem sujeitas às licenças originais. Antes de publicar `corpus_analise.csv`, confira as licenças de cada pacote.
