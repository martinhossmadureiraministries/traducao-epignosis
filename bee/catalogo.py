"""Catálogo canônico de 66 livros e numeração PalmBible+/MyBible."""
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Livro:
    numero: int
    nome: str
    arquivo: str
    abreviatura: str
    osis: str
    cor: str
    versos_por_capitulo: tuple[int, ...]

    @property
    def capitulos(self) -> int:
        return len(self.versos_por_capitulo)

    @property
    def antigo_testamento(self) -> bool:
        return self.numero < 470

    @property
    def nome_arquivo(self) -> str:
        return f"{self.numero:03d}_{self.arquivo}.json"


# Número MyBible, nome, nome ASCII para o ficheiro, abreviatura, ID OSIS.
# As lacunas numéricas são reservadas a livros fora deste cânone.
_DADOS = [
    (10, 'Gênesis', 'Genesis', 'Gn', 'Gen'),
    (20, 'Êxodo', 'Exodo', 'Êx', 'Exod'),
    (30, 'Levítico', 'Levitico', 'Lv', 'Lev'),
    (40, 'Números', 'Numeros', 'Nm', 'Num'),
    (50, 'Deuteronômio', 'Deuteronomio', 'Dt', 'Deut'),
    (60, 'Josué', 'Josue', 'Js', 'Josh'),
    (70, 'Juízes', 'Juizes', 'Jz', 'Judg'),
    (80, 'Rute', 'Rute', 'Rt', 'Ruth'),
    (90, '1 Samuel', '1_Samuel', '1Sm', '1Sam'),
    (100, '2 Samuel', '2_Samuel', '2Sm', '2Sam'),
    (110, '1 Reis', '1_Reis', '1Rs', '1Kgs'),
    (120, '2 Reis', '2_Reis', '2Rs', '2Kgs'),
    (130, '1 Crônicas', '1_Cronicas', '1Cr', '1Chr'),
    (140, '2 Crônicas', '2_Cronicas', '2Cr', '2Chr'),
    (150, 'Esdras', 'Esdras', 'Ed', 'Ezra'),
    (160, 'Neemias', 'Neemias', 'Ne', 'Neh'),
    (190, 'Ester', 'Ester', 'Et', 'Esth'),
    (220, 'Jó', 'Jo', 'Jó', 'Job'),
    (230, 'Salmos', 'Salmos', 'Sl', 'Ps'),
    (240, 'Provérbios', 'Proverbios', 'Pv', 'Prov'),
    (250, 'Eclesiastes', 'Eclesiastes', 'Ec', 'Eccl'),
    (260, 'Cânticos', 'Canticos', 'Ct', 'Song'),
    (290, 'Isaías', 'Isaias', 'Is', 'Isa'),
    (300, 'Jeremias', 'Jeremias', 'Jr', 'Jer'),
    (310, 'Lamentações', 'Lamentacoes', 'Lm', 'Lam'),
    (330, 'Ezequiel', 'Ezequiel', 'Ez', 'Ezek'),
    (340, 'Daniel', 'Daniel', 'Dn', 'Dan'),
    (350, 'Oseias', 'Oseias', 'Os', 'Hos'),
    (360, 'Joel', 'Joel', 'Jl', 'Joel'),
    (370, 'Amós', 'Amos', 'Am', 'Amos'),
    (380, 'Obadias', 'Obadias', 'Ob', 'Obad'),
    (390, 'Jonas', 'Jonas', 'Jn', 'Jonah'),
    (400, 'Miqueias', 'Miqueias', 'Mq', 'Mic'),
    (410, 'Naum', 'Naum', 'Na', 'Nah'),
    (420, 'Habacuque', 'Habacuque', 'Hc', 'Hab'),
    (430, 'Sofonias', 'Sofonias', 'Sf', 'Zeph'),
    (440, 'Ageu', 'Ageu', 'Ag', 'Hag'),
    (450, 'Zacarias', 'Zacarias', 'Zc', 'Zech'),
    (460, 'Malaquias', 'Malaquias', 'Ml', 'Mal'),
    (470, 'Mateus', 'Mateus', 'Mt', 'Matt'),
    (480, 'Marcos', 'Marcos', 'Mc', 'Mark'),
    (490, 'Lucas', 'Lucas', 'Lc', 'Luke'),
    (500, 'João', 'Joao', 'Jo', 'John'),
    (510, 'Atos', 'Atos', 'At', 'Acts'),
    (520, 'Romanos', 'Romanos', 'Rm', 'Rom'),
    (530, '1 Coríntios', '1_Corintios', '1Co', '1Cor'),
    (540, '2 Coríntios', '2_Corintios', '2Co', '2Cor'),
    (550, 'Gálatas', 'Galatas', 'Gl', 'Gal'),
    (560, 'Efésios', 'Efesios', 'Ef', 'Eph'),
    (570, 'Filipenses', 'Filipenses', 'Fp', 'Phil'),
    (580, 'Colossenses', 'Colossenses', 'Cl', 'Col'),
    (590, '1 Tessalonicenses', '1_Tessalonicenses', '1Ts', '1Thess'),
    (600, '2 Tessalonicenses', '2_Tessalonicenses', '2Ts', '2Thess'),
    (610, '1 Timóteo', '1_Timoteo', '1Tm', '1Tim'),
    (620, '2 Timóteo', '2_Timoteo', '2Tm', '2Tim'),
    (630, 'Tito', 'Tito', 'Tt', 'Titus'),
    (640, 'Filemom', 'Filemom', 'Fm', 'Phlm'),
    (650, 'Hebreus', 'Hebreus', 'Hb', 'Heb'),
    (660, 'Tiago', 'Tiago', 'Tg', 'Jas'),
    (670, '1 Pedro', '1_Pedro', '1Pe', '1Pet'),
    (680, '2 Pedro', '2_Pedro', '2Pe', '2Pet'),
    (690, '1 João', '1_Joao', '1Jo', '1John'),
    (700, '2 João', '2_Joao', '2Jo', '2John'),
    (710, '3 João', '3_Joao', '3Jo', '3John'),
    (720, 'Judas', 'Judas', 'Jd', 'Jude'),
    (730, 'Apocalipse', 'Apocalipse', 'Ap', 'Rev'),
]


def _cor(numero: int) -> str:
    if numero <= 50:
        return '#ccccff'
    if numero <= 190:
        return '#ffcc99'
    if numero <= 260:
        return '#66ff99'
    if numero <= 340:
        return '#ff9fb4'
    if numero <= 460:
        return '#ffff99'
    if numero <= 500:
        return '#ff6600'
    if numero == 510:
        return '#00ffff'
    if numero <= 650:
        return '#ffff00'
    if numero <= 720:
        return '#00ff00'
    return '#ff7c80'


with Path(__file__).with_name('versos_por_capitulo.json').open(encoding='utf-8') as _f:
    _contagens = json.load(_f)

LIVROS = tuple(
    Livro(num, nome, arquivo, abrev, osis, _cor(num), tuple(_contagens[osis]))
    for num, nome, arquivo, abrev, osis in _DADOS
)
POR_NUMERO = {livro.numero: livro for livro in LIVROS}
POR_OSIS = {livro.osis: livro for livro in LIVROS}

if len(LIVROS) != 66 or len(POR_NUMERO) != 66 or sum(l.capitulos for l in LIVROS) != 1189:
    raise RuntimeError('Catálogo bíblico inconsistente.')
