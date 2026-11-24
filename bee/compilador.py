"""Compila os dois módulos MyBible sem substituir uma versão boa em caso de erro."""
from __future__ import annotations

from html import escape
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import uuid
from typing import Any

from .arquivos import DadosInvalidos, ler_todos
from .catalogo import LIVROS, POR_NUMERO
from .fontes import ATRIBUICAO, AUTORIA
from .trava import trava


class ErroCompilacao(RuntimeError):
    pass


def _atribuicao_complementar(livros: dict[int, dict[str, Any]]) -> str:
    """Conserva no módulo as referências consultadas, sem incorporar as obras."""
    referencias: list[str] = []
    for numero in sorted(livros):
        if not livros[numero]['chapters']:
            continue
        for fonte in livros[numero].get('bibliography', []):
            titulo = fonte['name'].strip()
            revisao = fonte.get('revision')
            rotulo = f'{titulo} (revisão {revisao})' if revisao else titulo
            urls = [fonte[k] for k in ('url', 'text_url', 'apparatus_url') if fonte.get(k)]
            urls.extend(fonte.get('urls', []))
            item = rotulo + (': ' + ', '.join(urls) if urls else '')
            if fonte.get('license'):
                item += ' [licença: ' + fonte['license'] + ']'
            if fonte.get('attribution'):
                item += ' [atribuição: ' + fonte['attribution'] + ']'
            if item not in referencias:
                referencias.append(item)
    if not referencias:
        return ''
    return ' Referências adicionais consultadas (ver os JSON para utilização e licenças): ' + '; '.join(referencias) + '.'


def _metadados_revisao(livros: dict[int, dict[str, Any]]) -> tuple[str, str]:
    """Resume só os capítulos compilados; ausência de informação não é aprovação."""
    registros = []
    descricoes = []
    for numero, dados in sorted(livros.items()):
        if not dados['chapters']:
            continue
        capitulos = sorted(int(k) for k in dados['chapters'])
        total = sum(len(versos) for versos in dados['chapters'].values())
        revisao = dados.get('review', {})
        especialista = revisao.get('specialist', [])
        if isinstance(especialista, dict):
            especialista = [especialista]
        editoriais = [b for b in revisao.get('editorial_blocks', []) if b['chapter'] in capitulos]
        especialistas = [b for b in especialista if b['chapter'] in capitulos]

        def ausentes(blocos: list[dict[str, Any]]) -> int:
            # A validação já recusou intervalos sobrepostos ou fora do capítulo.
            return total - sum(b['verse_to'] - b['verse_from'] + 1 for b in blocos)

        def descricao(blocos: list[dict[str, Any]], desconhecidos: int) -> str:
            partes = []
            for b in blocos:
                primeiro, ultimo = b['verse_from'], b['verse_to']
                intervalo = str(primeiro) if primeiro == ultimo else f'{primeiro}–{ultimo}'
                partes.append(f"{b['chapter']}:{intervalo}: {b['status']}")
            if desconhecidos:
                partes.append(f'não informado em {desconhecidos} versículo(s)')
            return ', '.join(partes)

        nao_editorial = ausentes(editoriais)
        nao_especialista = ausentes(especialistas)
        registros.append({
            'book_number': numero, 'book_name': POR_NUMERO[numero].nome,
            'chapters_included': capitulos,
            'editorial_blocks': editoriais, 'specialist_blocks': especialistas,
            'editorial_unreported_verses': nao_editorial,
            'specialist_unreported_verses': nao_especialista,
        })
        descricoes.append(
            f"{POR_NUMERO[numero].nome} — editorial: {descricao(editoriais, nao_editorial)}; "
            f"especializada: {descricao(especialistas, nao_especialista)}"
        )
    texto = 'Estados informados para os trechos compilados: ' + ' | '.join(descricoes) + '.'
    return texto, json.dumps({'version': 1, 'books': registros}, ensure_ascii=False, separators=(',', ':'))


def _temporario(pasta: Path, prefixo: str) -> Path:
    fd, caminho = tempfile.mkstemp(prefix=prefixo, suffix='.bee-tmp', dir=pasta)
    os.close(fd)
    return Path(caminho)


def _criar_biblia(caminho: Path, livros: dict[int, dict[str, Any]], build_id: str, completo: bool, lacunas_fonte: int, pendentes: int = 0) -> int:
    conexao = sqlite3.connect(caminho)
    try:
        with conexao:
            conexao.executescript('''
                CREATE TABLE info (name TEXT, value TEXT);
                CREATE UNIQUE INDEX info_index ON info (name);
                CREATE TABLE books (book_number INTEGER, book_color TEXT, short_name TEXT, long_name TEXT);
                CREATE UNIQUE INDEX books_index ON books (book_number);
                CREATE TABLE books_all (book_number INTEGER, book_color TEXT, short_name TEXT, long_name TEXT, is_present BOOLEAN);
                CREATE UNIQUE INDEX books_all_index ON books_all (book_number);
                CREATE TABLE introductions (book_number INTEGER, introduction TEXT);
                CREATE UNIQUE INDEX introductions_index ON introductions (book_number);
                CREATE TABLE verses (book_number INTEGER, chapter INTEGER, verse INTEGER, text TEXT);
                CREATE UNIQUE INDEX verses_index ON verses (book_number, chapter, verse);
            ''')
            estado = 'RASCUNHO' if completo else 'RASCUNHO PARCIAL'
            referencias = AUTORIA + ' ' + ATRIBUICAO + _atribuicao_complementar(livros)
            resumo_revisao, revisao_json = _metadados_revisao(livros)
            aviso = (
                'Prévia produzida com IA para revisão, não edição final; '
                'os estados editoriais por trecho constam nos JSON quando informados. '
                'Revisão especializada necessária.'
            )
            info = {
                'description': f'Bíblia de Estudo Epignósis (BEE) — {estado}',
                'detailed_info': aviso + ' ' + resumo_revisao,
                'language': 'pt', 'russian_numbering': 'false', 'strong_numbers': 'false',
                'source': referencias,
                'bee_build_id': build_id,
                'bee_complete': str(completo).lower(),
                'bee_source_gaps': str(lacunas_fonte),
                'bee_pending_verses': str(pendentes),
                'bee_review_status': aviso,
                'bee_review_by_book': revisao_json,
            }
            conexao.executemany('INSERT INTO info (name, value) VALUES (?, ?)', info.items())
            introducao = ('<p><b>' + estado + ':</b> ' + escape(aviso) + '</p>'
                          '<p><b>Revisões informadas:</b> ' + escape(resumo_revisao) + '</p>'
                          '<p><b>Fontes, licenças e revisão:</b> ' + escape(referencias) + '</p>')
            conexao.execute('INSERT INTO introductions (book_number, introduction) VALUES (0, ?)', (introducao,))
            for livro in LIVROS:
                presente = livro.numero in livros and bool(livros[livro.numero]['chapters'])
                registro = (livro.numero, livro.cor, livro.abreviatura, livro.nome)
                conexao.execute('INSERT INTO books_all VALUES (?, ?, ?, ?, ?)', (*registro, int(presente)))
                if presente:
                    conexao.execute('INSERT INTO books VALUES (?, ?, ?, ?)', registro)
            registros = (
                (numero, int(capitulo), versiculo['verse'], versiculo['text'])
                for numero, dados in sorted(livros.items())
                for capitulo, versiculos in sorted(dados['chapters'].items(), key=lambda item: int(item[0]))
                for versiculo in versiculos
            )
            conexao.executemany('INSERT INTO verses (book_number, chapter, verse, text) VALUES (?, ?, ?, ?)', registros)
        total = conexao.execute('SELECT COUNT(*) FROM verses').fetchone()[0]
        if conexao.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ErroCompilacao('Verificação de integridade da Bíblia falhou.')
        return total
    finally:
        conexao.close()


def _criar_comentarios(caminho: Path, livros: dict[int, dict[str, Any]], build_id: str, completo: bool, lacunas_fonte: int, pendentes: int = 0) -> int:
    conexao = sqlite3.connect(caminho)
    try:
        with conexao:
            # A ordem dos sete campos iniciais segue o formato MyBible publicado.
            # book_number_to é um campo adicional solicitado pelo projeto; como
            # cada comentário cobre um único versículo, é igual a book_number.
            conexao.executescript('''
                CREATE TABLE info (name TEXT, value TEXT);
                CREATE UNIQUE INDEX info_index ON info (name);
                CREATE TABLE commentaries (
                    book_number INTEGER, chapter_number_from INTEGER, verse_number_from INTEGER,
                    chapter_number_to INTEGER, verse_number_to INTEGER, marker TEXT, text TEXT,
                    book_number_to INTEGER
                );
                CREATE UNIQUE INDEX commentaries_index ON commentaries
                    (book_number, chapter_number_from, verse_number_from);
            ''')
            estado = 'RASCUNHO' if completo else 'RASCUNHO PARCIAL'
            referencias = AUTORIA + ' ' + ATRIBUICAO + _atribuicao_complementar(livros)
            resumo_revisao, revisao_json = _metadados_revisao(livros)
            aviso = (
                'Prévia produzida com IA para revisão, não edição final; '
                'os estados editoriais por trecho constam nos JSON quando informados. '
                'Revisão especializada necessária.'
            )
            info = {
                'description': f'Comentários Exegéticos e Léxicos - BEE — {estado}',
                'detailed_info': aviso + ' ' + resumo_revisao + ' Fontes, licenças e revisão: ' + referencias,
                'language': 'pt', 'is_footnotes': 'false',
                'source': referencias,
                'bee_build_id': build_id,
                'bee_complete': str(completo).lower(),
                'bee_source_gaps': str(lacunas_fonte),
                'bee_pending_verses': str(pendentes),
                'bee_review_status': aviso,
                'bee_review_by_book': revisao_json,
            }
            conexao.executemany('INSERT INTO info (name, value) VALUES (?, ?)', info.items())
            registros = (
                (numero, int(capitulo), versiculo['verse'], int(capitulo), versiculo['verse'],
                 '', versiculo['commentary'], numero)
                for numero, dados in sorted(livros.items())
                for capitulo, versiculos in sorted(dados['chapters'].items(), key=lambda item: int(item[0]))
                for versiculo in versiculos if versiculo.get('commentary')
            )
            conexao.executemany(
                'INSERT INTO commentaries (book_number, chapter_number_from, verse_number_from, '
                'chapter_number_to, verse_number_to, marker, text, book_number_to) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                registros,
            )
        total = conexao.execute('SELECT COUNT(*) FROM commentaries').fetchone()[0]
        if conexao.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ErroCompilacao('Verificação de integridade dos comentários falhou.')
        return total
    finally:
        conexao.close()


def _publicar(pares: list[tuple[Path, Path]], pasta: Path) -> None:
    backups: dict[Path, Path | None] = {}
    publicados: list[Path] = []
    preservar: set[Path] = set()
    try:
        # Prepare os dois backups ANTES de substituir qualquer módulo.
        for _, destino in pares:
            if destino.exists():
                backup = _temporario(pasta, '.backup-bee-')
                backups[destino] = backup
                shutil.copy2(destino, backup)
            else:
                backups[destino] = None
        for origem, destino in pares:
            os.replace(origem, destino)
            publicados.append(destino)
    except BaseException as original:
        erros: list[str] = []
        for destino in reversed(publicados):
            backup = backups[destino]
            try:
                if backup is None:
                    destino.unlink(missing_ok=True)
                else:
                    os.replace(backup, destino)
            except OSError as exc:
                if backup is not None:
                    preservar.add(backup)
                    erros.append(f'{destino}: restaure manualmente {backup} ({exc})')
                else:
                    erros.append(f'{destino}: não foi possível remover o novo ficheiro ({exc})')
        if erros:
            raise ErroCompilacao('Falhou a reversão dos módulos: ' + '; '.join(erros)) from original
        raise
    finally:
        for backup in backups.values():
            if backup is not None and backup not in preservar:
                backup.unlink(missing_ok=True)


def compilar(diretorio_json: Path, diretorio_saida: Path) -> dict[str, int | bool | str]:
    # Duas pastas de dados distintas também não devem publicar ao mesmo tempo
    # no mesmo diretório de saída. A trava separada funciona mesmo se os
    # diretórios de dados e de saída forem iguais.
    with trava(diretorio_saida, nome='.bee.compile.lock'):
        return _compilar_travado(diretorio_json, diretorio_saida)


def _compilar_travado(diretorio_json: Path, diretorio_saida: Path) -> dict[str, int | bool | str]:
    livros = ler_todos(diretorio_json)
    capitulos = sum(len(dados['chapters']) for dados in livros.values())
    parciais = sum(len(dados.get('in_progress', {})) for dados in livros.values())
    if capitulos == 0:
        raise ErroCompilacao('Não há capítulos completos para compilar. Gere pelo menos um primeiro.')
    for numero, dados in livros.items():
        disponiveis = sorted(int(chave) for chave in dados['chapters'])
        if disponiveis and disponiveis != list(range(1, disponiveis[-1] + 1)):
            raise DadosInvalidos(
                f'{POR_NUMERO[numero].nome}: capítulos têm lacunas; MyBible requer capítulos consecutivos a partir de 1.'
            )
    lacunas_fonte = sum(
        v['text'].startswith('[Versículo sem texto correspondente no WLC consultado.]')
        for dados in livros.values() for versiculos in dados['chapters'].values() for v in versiculos
    )
    pendentes = sum(
        v['text'].startswith('[Versículo pendente:')
        for dados in livros.values() for versiculos in dados['chapters'].values() for v in versiculos
    )
    # Um capítulo com marcadores pendentes não conta como edição final, mesmo
    # que a estrutura tenha todos os capítulos.
    completo = capitulos == sum(l.capitulos for l in LIVROS) and pendentes == 0
    diretorio_saida.mkdir(parents=True, exist_ok=True)
    id_compilacao = uuid.uuid4().hex
    bible_temp = _temporario(diretorio_saida, '.BEE-')
    comentarios_temp = _temporario(diretorio_saida, '.BEE-comentarios-')
    try:
        total_versos = _criar_biblia(
            bible_temp, livros, id_compilacao, completo, lacunas_fonte, pendentes)
        total_comentarios = _criar_comentarios(
            comentarios_temp, livros, id_compilacao, completo, lacunas_fonte, pendentes)
        # Um comentário por versículo com nota; os versículos sem nota não entram no módulo.
        esperados_comentarios = sum(
            1 for dados in livros.values() for versiculos in dados['chapters'].values()
            for versiculo in versiculos if versiculo.get('commentary'))
        if total_versos == 0 or total_comentarios != esperados_comentarios:
            raise ErroCompilacao('Inconsistência entre os módulos; os ficheiros anteriores foram preservados.')
        _publicar([
            (bible_temp, diretorio_saida / 'BEE.SQLite3'),
            (comentarios_temp, diretorio_saida / 'BEE.commentaries.SQLite3'),
        ], diretorio_saida)
    except (OSError, sqlite3.Error) as exc:
        raise ErroCompilacao(f'Não foi possível compilar/publicar os módulos: {exc}') from exc
    finally:
        bible_temp.unlink(missing_ok=True)
        comentarios_temp.unlink(missing_ok=True)
    return {
        'livros': sum(bool(v['chapters']) for v in livros.values()),
        'capitulos': capitulos, 'parciais': parciais, 'versiculos': total_versos,
        'lacunas_fonte': lacunas_fonte, 'pendentes': pendentes,
        'completo': completo, 'build_id': id_compilacao,
    }
