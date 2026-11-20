#!/usr/bin/env python3
"""Migra as notas dos cinco livros curtos (Tito, Filemom, 2 João, 3 João, Judas).

Estado herdado de `scripts/importar_piloto.py`: o texto e a Síntese Exegética
vêm do piloto aprovado pelo responsável, mas a Análise Léxica e a Crítica
Textual são frases de enchimento («migração lexical pendente de verificação»,
«colação direta não repetida aqui»). Este script substitui-as por conteúdo
verificável, sem tocar no texto nem na Síntese:

* Análise Léxica — frases lexicais da própria nota do piloto aprovado
  (as frases de crítica textual ficam de fora; a Síntese mantém a nota inteira).
* Crítica Textual — gerada do aparato da SBLGNT (que nomeia apenas edições),
  da comparação com o Textus Receptus de Scrivener e, nos versículos com
  `CT_EXTRA`, de factos lidos no relatório de colação CNTR do livro
  (`docs/colacao/*.json`, gerado por `scripts/colar.py`). Nível de certeza
  A/B/C segundo `docs/CRITICA_TEXTUAL.md`: A quando a variante é apenas
  bizantina (RP) e as edições críticas (WH, Tregelles, NA28) apoiam a base;
  B quando as edições críticas se dividem; C nos casos em `NIVEL_C`.

Também acrescenta `sources`, `bibliography` e `review` (RASCUNHO) a estes
livros e a João 1, que os não tinham. Nada aqui aprova texto: os cinco livros
continuam RASCUNHO e as alterações ficam sinalizadas ao responsável.

Uso:
    python3 scripts/migrar_notas_cinco.py --prova     # prova de leitura
    python3 scripts/migrar_notas_cinco.py             # aplica
    python3 scripts/migrar_notas_cinco.py --verificar # confere invariantes
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

NOVA = RAIZ / 'edicoes' / 'nova' / 'livros_json'
PILOTO = RAIZ / 'edicoes' / 'piloto' / 'dados'
COLACAO = RAIZ / 'docs' / 'colacao'

# numero: (ficheiro na edição nova, ficheiro do piloto, relatório de colação)
LIVROS = {
    630: ('630_Tito.json', '630_Tito.json', 'Tito.json'),
    640: ('640_Filemom.json', '640_Filemom.json', 'Filemom.json'),
    700: ('700_2_Joao.json', '700_2_Joao.json', '2_João.json'),
    710: ('710_3_Joao.json', '710_3_Joao.json', '3_João.json'),
    720: ('720_Judas.json', '720_Judas.json', 'Judas.json'),
}

ENCHIMENTO_LEX = ('termos no original registados nas notas do piloto aprovado; '
                  'migração lexical pendente de verificação.')
ENCHIMENTO_CT = ('aparato de edições comparado no piloto aprovado; '
                 'colação direta não repetida aqui.')

# Frases inteiras da nota do piloto que são de crítica textual (não léxicas).
_MARCAS_TXT = re.compile(
    r'aparato|SBLGNT|\bKJV\b|\bESV\b|\bNIV\b|Textus|variante|manuscrito|'
    r'\bWH\b|\bNA2[78]\b|\bRP\b|edições|regista|imprime')

# Nível C: unidades em que a própria base é minoritária ou o texto é difícil.
NIVEL_C = {
    (720, 1, 5): 'as edições críticas dividem-se e <i>Ἰησοῦς</i> só tem NA28 '
                 'entre elas',
    (720, 1, 22): 'o verbo inicial e o arranjo das três cláusulas (vv. 22–23) '
                  'diferem entre WH e Tregelles/NA28/RP',
}

# Factos de colação escritos à mão a partir de docs/colacao/*.json (só
# testemunhas do acervo CNTR do próprio livro; ortografia não é citada).
CT_EXTRA = {
    (630, 1, 9): 'Na colação, 02 (Alexandrinus) substitui «no ensino sadio» por '
                 '<i>πάσῃ θλίψει</i> («em toda a tribulação»), leitura '
                 'singular que nenhuma edição segue.',
    (640, 1, 3): 'Na colação, 01 (Sinaiticus) omite <i>ἡμῶν</i> («nosso»). A '
                 'base lê <i>πατρὸς ἡμῶν</i> e a saudação mantém a fórmula '
                 'inteira, «Deus, nosso Pai» — ao contrário de 2 '
                 'Tessalonicenses 1:2, onde a base não tem <i>ἡμῶν</i> (ver '
                 'docs/CRITICA_TEXTUAL.md §9).',
    (640, 1, 6): 'Na colação, 02 e 04 omitem o artigo <i>τοῦ</i> com Tregelles, '
                 'e 01 lê <i>ὑμῖν</i> («em vocês») por <i>ἡμῖν</i> («em nós»), '
                 'com o Textus Receptus.',
    (640, 1, 7): 'Na colação, 01 omite «e consolação» — omissão singular, sem '
                 'apoio de nenhuma edição.',
    (720, 1, 5): 'Na colação das testemunhas, 03 (Vaticanus) e SR leem com a '
                 'base; 01 e 04 leem <i>κύριος</i> («o Senhor», 01 com '
                 '<i>ἅπαξ</i> deslocado) e P72 lê <i>θεὸς Χριστός</i> («Deus '
                 'Cristo»). É das unidades mais difíceis do Novo Testamento: '
                 'a decisão segue NA28 e fica assinalada para revisão '
                 'especializada.',
    (710, 1, 14): 'A divergência «a menos» das testemunhas colacionadas é de '
                  'numeração, não de texto: nelas a saudação final («Paz '
                  'contigo…») conta como v. 15, e a base também a regista '
                  'numa segunda entrada (3 João 1:15). O conteúdo é o mesmo.',
    (640, 1, 16): 'Na colação, 01 (Sinaiticus) omite <i>ἀδελφόν</i> («irmão»), '
                  'ficando só «amado»: omissão singular, sem apoio de edição.',
    (710, 1, 8): 'Na colação, 01 e 02 leem <i>τῇ ἐκκλησίᾳ</i> («da igreja») '
                 'onde a base lê <i>τῇ ἀληθείᾳ</i> («da verdade»); nenhuma '
                 'edição os segue e o texto mantém «cooperadores da verdade».',
    (720, 1, 12): 'Na colação, 02 e 04 leem <i>ἀπάταις</i> («enganos») onde a '
                  'base lê <i>ἀγάπαις</i> («refeições de amor»); 01, 03 e P72 '
                  'leem com a base. Nenhuma edição imprime <i>ἀπάταις</i> '
                  'aqui; é a palavra do paralelo de 2 Pedro 2:13, de onde '
                  'pode ter vindo por assimilação.',
    (720, 1, 14): 'Na colação, 01 e P72 leem «nas miríades dos santos anjos» '
                  '(<i>ἁγίων ἀγγέλων</i>) onde a base lê «nas suas santas '
                  'miríades»; 02, 03 e 04 leem com a base. Nenhuma edição '
                  'imprime a leitura dos anjos neste versículo.',
    (720, 1, 21): 'Na colação, 03, 04 e P72 leem o subjuntivo <i>τηρήσωμεν</i> '
                  '(«guardemo-nos») onde a base lê o imperativo '
                  '<i>τηρήσατε</i> («guarde-se»); 01 e 02 leem com a base e '
                  'nenhuma edição imprime o subjuntivo.',
    (720, 1, 23): 'A unidade que arranja as três cláusulas dos vv. 22–23 está '
                  'registada no v. 22; também neste versículo se segue a '
                  'base dessa unidade.',
}


def frases(texto: str) -> list[str]:
    texto = re.sub(r'<[^>]+>', '', texto or '').strip()
    partes = re.split(r'(?<=[.;])\s+', texto)
    return [p.strip() for p in partes if p.strip()]


def analise_lexica(nota_piloto: str) -> str:
    lex = [f for f in frases(nota_piloto) if not _MARCAS_TXT.search(f)]
    if not lex:
        raise SystemExit('nota do piloto sem frase lexical: ' + nota_piloto[:80])
    corpo = ' '.join(lex)
    if not corpo.endswith('.'):
        corpo += '.'
    return f'<p><b>Análise Léxica:</b> {corpo}</p>'


_SIGLAS = {'WH', 'Treg', 'NA28', 'NA27', 'RP', 'NIV', 'Holmes', 'WHmarg'}


def _dividir_apoio(parte: str) -> tuple[str, list[str]]:
    """'ἀδελφῇ WH Treg NA28' -> ('ἀδελφῇ', ['WH','Treg','NA28'])."""
    tokens = parte.strip().split()
    apoio: list[str] = []
    while tokens and tokens[-1] in _SIGLAS:
        apoio.insert(0, tokens.pop())
    return ' '.join(tokens), apoio


def _render_apoio(siglas: list[str]) -> str:
    nomes = {'Treg': 'Tregelles'}
    return ', '.join(nomes.get(s, s) for s in siglas) or 'sem apoio nomeado'


def critica_textual(numero: int, cap: int, verso: int, item_col: dict) -> str:
    base = item_col['base']
    aparato = base.get('aparato_sblgnt') or []
    frases_ct: list[str] = []
    apoios_variantes: list[set[str]] = []
    if aparato:
        descricoes = []
        for entrada in aparato:
            limpa = entrada.strip().lstrip('•').strip()
            limpa = re.sub(r'^[\d:–\-– ]+', '', limpa)  # referência inicial
            if ']' not in limpa:
                continue
            esq, dir_ = limpa.split(']', 1)
            leitura_base, apoio_base = _dividir_apoio(esq)
            variantes = []
            for alt in dir_.split(';'):
                leitura_alt, apoio_alt = _dividir_apoio(alt)
                if leitura_alt in ('–', '-'):
                    leitura_alt = 'omissão desta leitura'
                elif leitura_alt.startswith('+ '):
                    leitura_alt = 'acréscimo de ' + leitura_alt[2:]
                variantes.append((leitura_alt, apoio_alt))
                apoios_variantes.append(set(apoio_alt))
            texto_var = '; '.join(
                f'«{l}» ({_render_apoio(a)})' for l, a in variantes)
            descricoes.append(
                f'«{leitura_base}» ({_render_apoio(apoio_base)}) '
                f'contra {texto_var}')
        frases_ct.append(
            'O aparato da SBLGNT (que compara edições, não manuscritos) '
            'regista ' + '; '.join(descricoes) + '.')
        so_bizantina = all(a and a <= {'RP'} for a in apoios_variantes)
        if (numero, cap, verso) in NIVEL_C:
            nivel, razao = 'C', NIVEL_C[(numero, cap, verso)]
        elif so_bizantina:
            nivel, razao = 'A', ('a variante é bizantina (RP) e as edições '
                                 'críticas apoiam a base')
        else:
            nivel, razao = 'B', 'as edições críticas não são unânimes'
        frases_ct.append(
            f'O texto segue a base (nível de certeza {nivel}: {razao}).')
    else:
        igual_tr = base.get('sblgnt_norm') == base.get('scrivener_norm')
        frases_ct.append(
            'Sem unidade de variação adotada por qualquer edição: o aparato '
            'da SBLGNT nada regista neste versículo. Nas testemunhas '
            'colacionadas (CNTR) só há ortografia, abreviaturas de nomes '
            'sagrados ou leituras singulares que nenhuma edição imprime '
            '(relatório de colação do livro).')
        if igual_tr:
            frases_ct.append('O Textus Receptus de Scrivener lê o mesmo texto.')
        else:
            frases_ct.append(
                'O Textus Receptus de Scrivener diverge da base apenas em '
                'pormenor de forma ou de ordem, registado no mesmo relatório.')
    extra = CT_EXTRA.get((numero, cap, verso))
    if extra:
        frases_ct.append(extra)
    return '<p><b>Crítica Textual:</b> ' + ' '.join(frases_ct) + '</p>'


def secoes(comentario: str) -> list[tuple[str, str]]:
    """[(rótulo, parágrafo completo)] na ordem em que aparecem."""
    achados = []
    for m in re.finditer(r'<p><b>([^<]+):</b>.*?</p>', comentario or '', re.S):
        achados.append((m.group(1), m.group(0)))
    return achados


def migrar_livro(numero: int) -> tuple[dict, list[str]]:
    ficheiro, piloto_nome, col_nome = LIVROS[numero]
    livro = json.loads((NOVA / ficheiro).read_text(encoding='utf-8'))
    piloto = json.loads((PILOTO / piloto_nome).read_text(encoding='utf-8'))
    colacao = json.loads((COLACAO / col_nome).read_text(encoding='utf-8'))
    prova: list[str] = []
    for cap, versos in livro['chapters'].items():
        for v in versos:
            verso = v['verse']
            nota_piloto = piloto['chapters'][cap][verso - 1].get('commentary', '')
            item_col = colacao['versiculos'][f'{cap}:{verso}']
            lex = analise_lexica(nota_piloto)
            ct = critica_textual(numero, int(cap), verso, item_col)
            atuais = dict(secoes(v.get('commentary', '')))
            sintese = atuais.get('Síntese Exegética')
            if sintese is None:
                raise SystemExit(f'{numero} {cap}:{verso} sem Síntese')
            extras = [p for r, p in secoes(v.get('commentary', ''))
                      if r not in ('Análise Léxica', 'Crítica Textual',
                                   'Síntese Exegética')]
            v['commentary'] = lex + ct + sintese + ''.join(extras)
            prova.append(f'--- {numero} {cap}:{verso}\n{lex}\n{ct}')
    _completar_metadados(livro, numero, colacao, col_nome)
    return livro, prova


def _bibliografia(colacao: dict, col_nome: str, nome_livro: str) -> list[dict]:
    cntr = colacao['fontes']['cntr']
    testemunhas = ', '.join(cntr['manuscritos'])
    edicoes = ', '.join(cntr['edicoes'])
    return [
        {'name': 'SBLGNT — The Greek New Testament, SBL Edition',
         'revision': 'd7f35adca9ec410e1d1499c63b4dd989d76c8d4d',
         'url': 'https://github.com/Faithlife/SBLGNT',
         'text_url': 'https://codeload.github.com/Faithlife/SBLGNT/zip/d7f35adca9ec410e1d1499c63b4dd989d76c8d4d',
         'license': 'CC BY 4.0',
         'attribution': 'Base fixada do projeto. O aparato nomeia apenas '
                        'edições (WH, Treg, NA28, RP), nunca códices: as '
                        'afirmações sobre manuscritos vêm da colação CNTR.',
         'papel': 'base'},
        {'name': 'Textus Receptus — edição de Scrivener (Robinson)',
         'revision': '6049a43b135ed870f843b83eb6a04764fc796678',
         'url': 'https://github.com/byztxt/greektext-scrivener',
         'text_url': 'https://codeload.github.com/byztxt/greektext-scrivener/zip/6049a43b135ed870f843b83eb6a04764fc796678',
         'license': 'domínio público segundo o fornecedor',
         'attribution': 'Comparação, não base. «O Textus Receptus» não é um '
                        'texto único: esta edição difere de RP e do KJTR.',
         'papel': 'comparação'},
        {'name': 'CNTR Transcriptions (Center for New Testament Restoration)',
         'revision': cntr['revisao'],
         'url': cntr['url'],
         'license': 'CC BY-SA 4.0',
         'attribution': f"Alan Bunning / Center for New Testament Restoration. "
                        f"Testemunhas de {nome_livro} consultadas: "
                        f"{testemunhas}; textos críticos: {edicoes}. Custódia: "
                        'o acervo vive em .bee-cache/ (excluída pelo '
                        '.gitignore) — é consultado e citado, nunca '
                        'redistribuído; só o relatório de colação é versionado.',
         'papel': 'testemunhas e textos críticos'},
        {'name': f'Relatório de colação de {nome_livro} (obra do projeto)',
         'url': f'docs/colacao/{col_nome}',
         'attribution': 'Gerado por scripts/colar.py com bee/manuscritos.py. '
                        'É a evidência verificável de cada afirmação sobre '
                        'manuscritos destas notas: uma linha do relatório por '
                        'testemunha citada. O protocolo está em '
                        'docs/CRITICA_TEXTUAL.md.',
         'papel': 'evidência'},
    ]


def _completar_metadados(livro: dict, numero: int, colacao: dict,
                         col_nome: str) -> None:
    nome = livro['book_name']
    livro['sources'] = {
        'versification': 'KJV/tradicional',
        'alignment_version': 1,
        'sblgnt_commit': 'd7f35adca9ec410e1d1499c63b4dd989d76c8d4d',
        'textus_receptus_commit': '6049a43b135ed870f843b83eb6a04764fc796678',
        'cntr_transcriptions_commit': '4e743a41a4b2ca010ece53229cd272aa59b1efe6',
        'collation_report': f'docs/colacao/{col_nome}',
    }
    livro['bibliography'] = _bibliografia(colacao, col_nome, nome)
    total = sum(len(vs) for vs in livro['chapters'].values())
    nota_ed = (
        'Texto do piloto aprovado pelo responsável, importado por '
        'scripts/importar_piloto.py. Em 2026-11-20 as notas foram migradas '
        'por scripts/migrar_notas_cinco.py: a Análise Léxica vem das notas '
        'do piloto e a Crítica Textual foi escrita da base fixada (SBLGNT '
        'd7f35ad), do seu aparato e da colação CNTR do livro. Continua '
        'RASCUNHO até leitura do responsável.')
    blocos_ed, blocos_esp, historico = [], [], []
    for cap, versos in sorted(livro['chapters'].items(), key=lambda kv: int(kv[0])):
        n = len(versos)
        blocos_ed.append({'chapter': int(cap), 'verse_from': 1, 'verse_to': n,
                          'status': 'rascunho', 'nota': nota_ed})
        blocos_esp.append({'chapter': int(cap), 'verse_from': 1, 'verse_to': n,
                           'status': 'pendente'})
        historico.append({'chapter': int(cap), 'verse_from': 1, 'verse_to': n,
                          'provider': 'local',
                          'model': 'editorial:migracao-notas-cinco-livros',
                          'generated_at_utc': '2026-11-20T12:30:00+00:00'})
    livro['review'] = {'editorial_blocks': blocos_ed, 'specialist': blocos_esp}
    livro.setdefault('history', []).extend(historico)


def completar_joao() -> dict:
    livro = json.loads((NOVA / '500_Joao.json').read_text(encoding='utf-8'))
    colacao = json.loads((COLACAO / 'João.json').read_text(encoding='utf-8'))
    cntr = colacao['fontes']['cntr']
    livro['sources'].update({
        'cntr_transcriptions_commit': '4e743a41a4b2ca010ece53229cd272aa59b1efe6',
        'collation_report': 'docs/colacao/João.json'})
    livro['bibliography'] = _bibliografia(colacao, 'João.json', 'João')
    nota_ed = (
        'Capítulo 1 lapidado em 2026-11-20 por scripts/lapidar_seis.py sobre '
        'a base fixada (SBLGNT d7f35ad) e o seu aparato; as notas de crítica '
        'textual citam apenas edições do aparato e, com nível de certeza, '
        'as decisões registadas. Bibliografia e revisão acrescentadas por '
        'scripts/migrar_notas_cinco.py. Continua RASCUNHO.')
    livro['review'] = {
        'editorial_blocks': [{'chapter': 1, 'verse_from': 1, 'verse_to': 51,
                              'status': 'rascunho', 'nota': nota_ed}],
        'specialist': [{'chapter': 1, 'verse_from': 1, 'verse_to': 51,
                        'status': 'pendente',
                        'nota': 'Prioridade: 1:18 (μονογενὴς θεός) e 1:34 '
                                '(ἐκλεκτός, nível C).'}]}
    livro.setdefault('history', []).append(
        {'chapter': 1, 'verse_from': 1, 'verse_to': 51, 'provider': 'local',
         'model': 'editorial:migracao-notas-cinco-livros',
         'generated_at_utc': '2026-11-20T12:30:00+00:00'})
    return livro


def verificar() -> None:
    erros = []
    for ficheiro in sorted(NOVA.glob('*.json')):
        livro = json.loads(ficheiro.read_text(encoding='utf-8'))
        for cap, versos in livro['chapters'].items():
            for v in versos:
                c = v.get('commentary', '') or ''
                ref = f"{ficheiro.name} {cap}:{v['verse']}"
                if ENCHIMENTO_LEX in c or ENCHIMENTO_CT in c:
                    erros.append(f'{ref}: enchimento por migrar')
                rotulos = [r for r, _ in secoes(c)]
                for obrig in ('Análise Léxica', 'Crítica Textual',
                              'Síntese Exegética'):
                    if obrig not in rotulos:
                        erros.append(f'{ref}: falta {obrig}')
        if not livro.get('bibliography'):
            erros.append(f'{ficheiro.name}: sem bibliography')
        if not livro.get('review'):
            erros.append(f'{ficheiro.name}: sem review')
    if erros:
        print('\n'.join(erros))
        raise SystemExit(1)
    print('OK: notas migradas, três secções, bibliography e review nos sete livros.')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prova', action='store_true')
    ap.add_argument('--verificar', action='store_true')
    args = ap.parse_args()
    if args.verificar:
        verificar()
        return
    provas: list[str] = []
    saidas: dict[Path, dict] = {}
    for numero in LIVROS:
        livro, prova = migrar_livro(numero)
        saidas[NOVA / LIVROS[numero][0]] = livro
        provas.extend(prova)
    saidas[NOVA / '500_Joao.json'] = completar_joao()
    if args.prova:
        print('\n'.join(provas))
        return
    for caminho, livro in saidas.items():
        caminho.write_text(
            json.dumps(livro, ensure_ascii=False, indent=1) + '\n',
            encoding='utf-8')
        total = sum(len(vs) for vs in livro['chapters'].values())
        print(f'{caminho.name}: notas migradas em {total} versículos.')


if __name__ == '__main__':
    main()
