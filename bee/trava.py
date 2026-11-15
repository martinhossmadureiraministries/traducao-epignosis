"""Trava de processo; o sistema operacional liberta-a em caso de interrupção."""
from contextlib import contextmanager
from pathlib import Path


class EmExecucao(RuntimeError):
    pass


@contextmanager
def trava(diretorio: Path, nome: str = '.bee.lock'):
    diretorio.mkdir(parents=True, exist_ok=True)
    caminho = diretorio / nome
    with caminho.open('a+b') as arquivo:
        try:
            if __import__('os').name == 'nt':
                import msvcrt
                arquivo.seek(0)
                if not arquivo.read(1):
                    arquivo.write(b'0')
                    arquivo.flush()
                arquivo.seek(0)
                try:
                    msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as exc:
                    raise EmExecucao(f'Já existe uma execução a usar {diretorio}.') from exc
            else:
                import fcntl
                try:
                    fcntl.flock(arquivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise EmExecucao(f'Já existe uma execução a usar {diretorio}.') from exc
            yield
        finally:
            # Fechar o descritor é suficiente para soltar a trava, inclusive no Windows.
            pass
