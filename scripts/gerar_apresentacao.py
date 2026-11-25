#!/usr/bin/env python3
"""Gera docs/APRESENTACAO_BEE.docx — o documento de apresentação atual da BEE.

Os números e a tabela de estado vêm dos JSON da edição nova (não de texto fixo),
para que o documento não possa contradizer os dados. O texto de método e de
voz descreve o processo vigente (docs/EDICAO_NOVA.md, docs/ESTILO_BEE.md).

Dependência opcional, só para este script:
    pip install python-docx
Uso:
    python3 scripts/gerar_apresentacao.py [--saida docs/APRESENTACAO_BEE.docx]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.catalogo import LIVROS, POR_NUMERO  # noqa: E402

SAIDA = RAIZ / 'docs' / 'APRESENTACAO_BEE.docx'
DADOS = RAIZ / 'edicoes' / 'nova' / 'livros_json'
DATA = '20 de novembro de 2026'
META_CAPITULOS = 1189
META_VERSICULOS = 31102


def carregar_livros(pasta: Path = DADOS) -> list[dict]:
    """Um resumo por JSON: capítulos, versículos e estados de revisão."""
    resumo = []
    for caminho in sorted(pasta.glob('*.json')):
        dados = json.loads(caminho.read_text(encoding='utf-8'))
        revisao = dados.get('review') or {}
        blocos = revisao.get('editorial_blocks') or []
        especializada = revisao.get('specialist') or []
        ministerio = (revisao.get('ministerio') or {}).get('status', 'sem registo')
        versiculos = sum(len(v) for v in dados['chapters'].values())
        resumo.append({
            'numero': int(dados['book_number']),
            'nome': POR_NUMERO[int(dados['book_number'])].nome,
            'capitulos': len(dados['chapters']),
            'versiculos': versiculos,
            'editorial': all(str(b.get('status', '')).startswith('aprovado') for b in blocos) and bool(blocos),
            'especializada': 'pendente' if all(b.get('status') == 'pendente' for b in especializada) and especializada
                             else 'registada',
            'ministerio': ministerio,
        })
    return sorted(resumo, key=lambda r: r['numero'])


def _milhares(n: int) -> str:
    return f'{n:,}'.replace(',', '.')


def _sim_nao(valor: bool) -> str:
    return 'aprovado' if valor else 'pendente'


def construir(livros: list[dict] | None = None):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor

    livros = carregar_livros() if livros is None else livros
    capitulos = sum(r['capitulos'] for r in livros)
    versiculos = sum(r['versiculos'] for r in livros)
    total_livros = len(LIVROS)
    azul = RGBColor(0x1F, 0x3A, 0x5F)

    doc = Document()
    estilo = doc.styles['Normal']
    estilo.font.name = 'Calibri'
    estilo.font.size = Pt(11)

    def p(texto: str, **kw):
        para = doc.add_paragraph(texto)
        if kw.get('centro'):
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return para

    def lista(itens: list[str]):
        for item in itens:
            doc.add_paragraph(item, style='List Bullet')

    def tabela(cabecalho: list[str], linhas: list[list[str]]):
        t = doc.add_table(rows=1, cols=len(cabecalho))
        t.style = 'Table Grid'
        for i, texto in enumerate(cabecalho):
            celula = t.rows[0].cells[i]
            celula.text = texto
            for r in celula.paragraphs[0].runs:
                r.bold = True
        for linha in linhas:
            cels = t.add_row().cells
            for i, texto in enumerate(linha):
                cels[i].text = texto
        doc.add_paragraph()

    # ---------- capa ----------
    titulo = doc.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = titulo.add_run('BÍBLIA DE ESTUDO EPIGNÓSIS')
    r.bold = True
    r.font.size = Pt(22)
    r.font.color.rgb = azul
    p('Documento de apresentação', centro=True)
    p('Autor e responsável editorial: Martinho S. S. Madureira', centro=True)
    p('Publicado por: Martinho S. S. Madureira Ministries', centro=True)
    p(f'Documento gerado em {DATA}', centro=True)
    doc.add_paragraph()
    n_ministerio = sum(r['ministerio'].startswith('aprovado') for r in livros)
    aviso = p('Estado da obra: RASCUNHO em produção. Nenhum livro é edição final: '
              'a revisão especializada (por especialista externo) está pendente em todos os '
              f'livros; a revisão aprovada pelo ministério está registada em {n_ministerio} de '
              f'{len(livros)}.', centro=True)
    for r in aviso.runs:
        r.italic = True

    # ---------- 1 ----------
    doc.add_heading('1. O que é a BEE', level=1)
    p(f'A BEE é uma Bíblia de estudo em português contemporâneo, para os 66 livros do '
      f'cânone escolhido ({_milhares(META_CAPITULOS)} capítulos e {_milhares(META_VERSICULOS)} '
      f'versículos ao todo, meta do projeto). O texto é traduzido diretamente do grego e do '
      f'hebraico fixados, e não a partir de outra tradução.')
    p('A nota em prosa é opcional: onde há algo a explicar, traz a palavra original decisiva, a '
      'razão da escolha feita e a alternativa rejeitada. Um acréscimo em itálico ou uma variante '
      'marcada no texto exigem sempre nota. Quando a colação de manuscritos ou o aparato regista '
      'uma variante, a nota tem um parágrafo próprio, «Crítica Textual», que diz o que a variante '
      'muda e porque a base foi seguida.')
    p('O destino previsto são os módulos para a aplicação MyBible (BEE.SQLite3 para o texto e '
      'BEE.commentaries.SQLite3 para as notas). A compilação existe no repositório e só inclui '
      'capítulos completos e consecutivos desde o capítulo 1. Os módulos saem marcados como '
      'rascunho.')

    # ---------- 2 ----------
    doc.add_heading('2. Estado em 20 de novembro de 2026', level=1)
    aprovados = [r for r in livros if r['editorial']]
    p(f'Edição nova: {len(livros)} livros, {capitulos} capítulos e {versiculos} versículos em '
      f'prosa, de {total_livros} livros do catálogo. Os outros {total_livros - len(livros)} '
      f'livros ainda não têm edição nova. Dos {len(livros)} livros com edição, '
      f'{len(aprovados)} estão aprovados editorialmente pelo responsável.')
    tabela(['Livro', 'Capítulos', 'Versículos', 'Revisão editorial', 'Revisão especializada',
            'Revisão do ministério'],
           [[r['nome'], str(r['capitulos']), str(r['versiculos']),
             _sim_nao(r['editorial']),
             'pendente' if r['especializada'] == 'pendente' else 'registada',
             _sim_nao(r['ministerio'].startswith('aprovado'))] for r in livros])
    p('A revisão especializada está pendente em todos os livros, a cargo de especialista externo. '
      'A revisão aprovada pelo ministério é uma etapa própria, aplicada aos livros com edição nova: '
      f'está registada em {n_ministerio} e pendente nos outros {len(livros) - n_ministerio}.')

    # ---------- 3 ----------
    doc.add_heading('3. Três revisões, nunca confundidas', level=1)
    lista([
        'Revisão editorial: o responsável lê cada livro (ou amostra), aprova ou manda refazer. '
        'A aprovação fica registada no próprio JSON, bloco a bloco, com a data e a nota.',
        'Revisão especializada: feita por especialista externo (hebraísta, grego, crítico textual '
        'ou teólogo). Ainda não foi iniciada. É condição de publicação final.',
        'Revisão aprovada pelo ministério: feita por Martinho S. S. Madureira Ministries, como '
        'etapa própria. Aplica-se aos livros com edição nova; está pendente onde não foi registada.',
    ])
    p('Não há revisão por inteligência artificial. Nenhum agente aprova em nome do responsável.')

    # ---------- 4 ----------
    doc.add_heading('4. Como se produz', level=1)
    lista([
        'Textos-base fixados: o SBLGNT (CC BY 4.0) para o Novo Testamento, com o Textus Receptus '
        'de Scrivener só como comparação; o Westminster Leningrad Codex, por meio da Open Scriptures '
        'Hebrew Bible, para o Antigo Testamento.',
        'Colação: cada testemunha citada numa nota tem de constar da colação do livro '
        '(docs/colacao/). Edição impressa não é manuscrito, e tradução moderna não é evidência textual.',
        'Redação no repositório, com assistência de inteligência artificial, sob direção editorial '
        'do responsável. Não há produção automática por serviços de IA.',
        'Verificações automáticas: integridade dos dados, estilo e arcaísmos, convenções das notas, '
        'notas contra a colação, ortografia (como alerta) e coerência da documentação. Estas '
        'verificações não substituem a leitura nem a revisão especializada.',
        'Todo o trabalho fica em Git, no repositório público, com o histórico de cada decisão.',
    ])

    # ---------- 5 ----------
    doc.add_heading('5. A voz', level=1)
    p('Clareza para ler, cadência para proclamar, profundidade para estudar. O impacto deve vir '
      'do texto, não de frases acrescentadas. Exemplo de nota, Filipenses 2:6 (aprovado editorialmente; '
      'revisão especializada pendente):')
    p('Texto: «que, existindo em forma de Deus, não considerou o ser igual a Deus algo a que se '
      'agarrasse».', ).runs[0].italic = True
    p('Nota: «ἁρπαγμός é a palavra mais discutida do hino. (…) A BEE escolhe a imagem do gesto — '
      '«algo a que se agarrasse» — porque mantém as duas pontas: não nega a igualdade (que μορφὴ '
      'θεοῦ afirma), nega o agarramento.»')
    lista([
        'Português europeu, com o Acordo Ortográfico de 1990.',
        'Palavras acrescentadas sem correspondência no grego ficam em itálico. Os colchetes ficam '
        'só para o que a evidência dos manuscritos pede.',
        'As notas são prosa, sem rótulos e sem níveis de certeza impressos.',
        'O tratamento do leitor segue a norma do texto: «vocês» no plural natural, e concordância '
        'consistente quando se usa «tu».',
        'Nenhuma nota inventa etimologias, testemunhas ou revisões que não aconteceram, e nenhuma '
        'contradiz o versículo que comenta.',
    ])

    # ---------- 6 ----------
    doc.add_heading('6. Decisões de texto já tomadas pelo responsável', level=1)
    tabela(['Passagem', 'Decisão'], [
        ['João 4:1', '«Jesus» no texto; «o Senhor», a alternativa da base, fica na nota.'],
        ['João 14:26, 15:26, 16:7', '«Parácletos» (nominativo), transliteração literal de παράκλητος.'],
        ['João 14:16', '«Parácleton» (acusativo).'],
        ['João 16:25 e 16:29', '«com clareza» (e não «franqueza»).'],
        ['João 20:15', '«Jardineiro» (κηπουρός), no lugar de «hortelão».'],
        ['João 20:17', '«Não me segures» (ἅπτου), mantido.'],
        ['João 21:15–17', '«amas-me» (ἀγαπᾷς) e «queres-me bem» (φιλεῖς); «mais do que estes» em 21:15.'],
        ['Nomes próprios', 'Getsêmani, Gólgota, Arimateia, Clopas, Madalena, Caifás, Pilatos, Anás, Cedrom, Malco e Barrabás.'],
    ])

    # ---------- 7 ----------
    doc.add_heading('7. O que falta e próximos passos', level=1)
    lista([
        f'Revisão especializada dos {len(livros)} livros, por especialista externo.',
        f'Revisão aprovada pelo ministério: faltam {len(livros) - n_ministerio} livros com edição nova.',
        'Próximo livro: 1 João (105 versículos), com colação feita; texto ainda por redigir. '
        'A ordem das cartas segue os livros menores primeiro, com prioridade para os que fixam a voz '
        'e o vocabulário (ver docs/RESUMO_ESTILO.md, secção 10).',
        f'{total_livros - len(livros)} livros do catálogo ainda sem edição nova, incluindo o Antigo '
        'Testamento inteiro.',
        'Passagens em aberto registadas no repositório, por exemplo Marcos 16:9–20.',
    ])

    # ---------- 8 ----------
    doc.add_heading('8. Limites e avisos', level=1)
    lista([
        'Esta obra é um rascunho. Não é edição final, não substitui a revisão especializada e não '
        'é produto oficial nem aprovado pelo MyBible.',
        'Os erros possíveis de tradução, de transliteração, de crítica textual e de atribuição a '
        'léxicos continuam a ser responsabilidade da revisão humana. A validação automática verifica '
        'estrutura e marcação, não fidelidade teológica ou filológica.',
        'Licenças: o SBLGNT é CC BY 4.0; o acervo CNTR é CC BY-SA 4.0, consultado e citado, nunca '
        'redistribuído. As atribuições ficam nos JSON e nos módulos.',
    ])

    # ---------- fim ----------
    doc.add_page_break()
    fim = doc.add_paragraph()
    fim.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fim.add_run('— Fim do documento de apresentação —')
    r.bold = True
    r.font.color.rgb = azul
    return doc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--saida', type=Path, default=SAIDA)
    args = ap.parse_args()
    try:
        import docx  # noqa: F401
    except ImportError:
        print('ERRO: falta python-docx. Instalar com: pip install python-docx', file=sys.stderr)
        return 1
    doc = construir()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    doc.save(args.saida)
    print(f'Escrito: {args.saida}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
