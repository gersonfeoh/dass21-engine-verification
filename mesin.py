# -*- coding: utf-8 -*-
"""Mesin acuan DASS-21 menurut manual Lovibond dan Lovibond (1995), beserta mutannya.

Satu-satunya masukan adalah vektor 21 butir bernilai 0 sampai 3. Keluaran adalah
kategori ketiga subskala, keputusan gerbang kelayakan pendamping, dan penanda eskalasi.

Spesifikasi gerbang dan penanda mengikuti PRD aplikasi (bagian 6.2 dan 6.3):
- gerbang terbuka bila kategori ketiga subskala pada skrining terakhir Normal;
- penanda PERLU_PERHATIAN bila kategori Depresi Severe atau Extremely Severe,
  ATAU butir 10, 17, atau 21 bernilai 3 (butir keputusasaan dan ketidakberhargaan).
"""
import itertools

BUTIR = {  # nomor butir 1..21
    'D': (3, 5, 10, 13, 16, 17, 21),
    'A': (2, 4, 7, 9, 15, 19, 20),
    'S': (1, 6, 8, 11, 12, 14, 18),
}
# batas bawah kategori Mild, Moderate, Severe, Extremely Severe pada skor yang sudah dikali dua
BATAS = {'D': (10, 14, 21, 28), 'A': (8, 10, 15, 20), 'S': (15, 19, 26, 34)}
KATEGORI = ('Normal', 'Mild', 'Moderate', 'Severe', 'Extremely Severe')
SUB = ('D', 'A', 'S')
BUTIR_KRITIS = (10, 17, 21)


def kategori(skor, batas):
    k = 0
    for b in batas:
        if skor >= b:
            k += 1
    return k   # 0 = Normal ... 4 = Extremely Severe


class Mesin:
    """Mesin yang dapat dimutasi lewat parameter, tidak lewat penyuntingan kode."""

    def __init__(self, butir=None, batas=None, faktor=2, gerbang='semua_normal',
                 gerbang_sub=SUB, penanda_min=3, penanda_sub=('D',),
                 butir_kritis=BUTIR_KRITIS, butir_min=3, penanda_gabung='atau',
                 nama='acuan'):
        self.butir = butir or BUTIR
        self.batas = batas or BATAS
        self.faktor = faktor
        self.gerbang = gerbang
        self.gerbang_sub = gerbang_sub
        self.penanda_min = penanda_min
        self.penanda_sub = penanda_sub
        self.butir_kritis = butir_kritis
        self.butir_min = butir_min
        self.penanda_gabung = penanda_gabung
        self.nama = nama

    def skor(self, x):
        return {s: self.faktor * sum(x[i - 1] for i in self.butir[s]) for s in SUB}

    def kritis(self, x):
        return any(x[i - 1] >= self.butir_min for i in self.butir_kritis)

    def dari_skor(self, sk, kritis=False):
        kat = {s: kategori(sk[s], self.batas[s]) for s in SUB}
        if self.gerbang == 'semua_normal':
            g = all(kat[s] == 0 for s in self.gerbang_sub)
        elif self.gerbang == 'salah_satu_normal':
            g = any(kat[s] == 0 for s in self.gerbang_sub)
        elif self.gerbang == 'maks_mild':
            g = all(kat[s] <= 1 for s in self.gerbang_sub)
        pk = any(kat[s] >= self.penanda_min for s in self.penanda_sub)
        if self.penanda_gabung == 'atau':
            p = pk or kritis
        elif self.penanda_gabung == 'dan':
            p = pk and kritis
        elif self.penanda_gabung == 'kategori_saja':
            p = pk
        elif self.penanda_gabung == 'butir_saja':
            p = kritis
        return (kat['D'], kat['A'], kat['S'], g, p)

    def __call__(self, x):
        return self.dari_skor(self.skor(x), self.kritis(x))


def mutan():
    """Kumpulan mutan sistematis, dikelompokkan menurut kelas kesalahan."""
    out = []
    # M1 kesalahan ambang: tiap batas digeser -2, -1, +1, +2
    for s in SUB:
        for j in range(4):
            for d in (-2, -1, 1, 2):
                b = {k: list(v) for k, v in BATAS.items()}
                b[s][j] += d
                if j > 0 and b[s][j] <= b[s][j - 1]:
                    continue
                if j < 3 and b[s][j] >= b[s][j + 1]:
                    continue
                out.append(('M1 ambang', Mesin(batas={k: tuple(v) for k, v in b.items()},
                                              nama='%s batas%d %+d' % (s, j + 1, d))))
    # M2 kesalahan faktor pengali
    out.append(('M2 faktor', Mesin(faktor=1, nama='tanpa kali dua')))
    out.append(('M2 faktor', Mesin(faktor=4, nama='kali dua ganda')))
    # M3 kesalahan pemetaan butir: satu butir dihitung pada subskala lain
    for s in SUB:
        for i in BUTIR[s]:
            for t in SUB:
                if t == s:
                    continue
                bt = {k: list(v) for k, v in BUTIR.items()}
                bt[s].remove(i); bt[t].append(i)
                out.append(('M3 pemetaan butir', Mesin(butir={k: tuple(v) for k, v in bt.items()},
                                                       nama='butir %d %s ke %s' % (i, s, t))))
    # M4 kesalahan gerbang kelayakan
    out.append(('M4 gerbang', Mesin(gerbang='salah_satu_normal', nama='gerbang OR')))
    out.append(('M4 gerbang', Mesin(gerbang='maks_mild', nama='gerbang sampai Mild')))
    for s in SUB:
        out.append(('M4 gerbang', Mesin(gerbang_sub=tuple(x for x in SUB if x != s),
                                        nama='gerbang abaikan %s' % s)))
    # M5 kesalahan penanda eskalasi
    out.append(('M5 penanda', Mesin(penanda_min=2, nama='penanda kategori mulai Moderate')))
    out.append(('M5 penanda', Mesin(penanda_min=4, nama='penanda kategori hanya Extremely Severe')))
    out.append(('M5 penanda', Mesin(penanda_sub=SUB, nama='penanda kategori pada subskala mana pun')))
    out.append(('M5 penanda', Mesin(penanda_gabung='dan', nama='penanda konjungsi')))
    out.append(('M5 penanda', Mesin(penanda_gabung='kategori_saja', nama='penanda tanpa aturan butir')))
    out.append(('M5 penanda', Mesin(penanda_gabung='butir_saja', nama='penanda tanpa aturan kategori')))
    out.append(('M5 penanda', Mesin(butir_min=2, nama='penanda butir mulai nilai 2')))
    for i in BUTIR_KRITIS:
        out.append(('M5 penanda', Mesin(butir_kritis=tuple(j for j in BUTIR_KRITIS if j != i),
                                        nama='penanda abaikan butir %d' % i)))
    return out


def kisi():
    """Semua skor yang dapat dicapai per subskala: 0, 2, ..., 42."""
    return list(range(0, 43, 2))
