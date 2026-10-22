# -*- coding: utf-8 -*-
"""Rangkaian uji dan analisis mutasi untuk mesin DASS-21.

Seluruh angka yang dihasilkan skrip ini adalah hasil komputasi atas mesin acuan dan
mutannya. Tidak ada data responden yang dipakai.
"""
import itertools, json, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mesin import Mesin, mutan, kisi, BUTIR, BATAS, SUB, KATEGORI, kategori, BUTIR_KRITIS

ACUAN = Mesin()
KISI = kisi()


# ------------------------------------------------------------ 1. pemeriksaan tabel acuan
def periksa_tabel():
    """Pemeriksaan partisi gaya Rahaman dkk.: cakupan dan tanpa tumpang tindih."""
    hasil = {}
    for s in SUB:
        b = BATAS[s]
        pita = [(0, b[0] - 1), (b[0], b[1] - 1), (b[1], b[2] - 1), (b[2], b[3] - 1), (b[3], 42)]
        bulat = set(range(43))
        cakup = set(); tumpang = 0
        for lo, hi in pita:
            r = set(range(lo, hi + 1))
            tumpang += len(cakup & r); cakup |= r
        genap = [[v for v in KISI if lo <= v <= hi] for lo, hi in pita]
        hasil[s] = dict(
            pita=pita,
            cakupan_bulat=(cakup == bulat), tumpang_tindih=tumpang,
            titik_genap=[len(g) for g in genap],
            nilai_genap=genap,
            batas_ganjil=[c for c in b if c % 2 == 1],
        )
    return hasil


# ------------------------------------------------------------ 2. konstruksi vektor butir
def vektor(target, cara, k=0):
    """Bangun vektor 21 butir yang menghasilkan skor target (kali dua) tiap subskala.

    cara 'depan' : beban diisi dari butir pertama daftar subskala (cara yang lazim).
    cara 'putar' : butir awal pengisian digeser sebesar k, sehingga beban berpindah
                   ke butir yang berbeda pada tiap kasus uji.
    cara 'isolasi': seperti 'putar', tetapi pada subskala Depresi beban diisi lebih dulu
                   ke butir non-kritis, lalu butir kritis paling tinggi 2, dan baru dinaikkan
                   ke 3 bila skor target tidak dapat dicapai tanpa itu. Dengan begitu kondisi
                   kategori Depresi dan kondisi butir kritis pada aturan penanda terpisah.
    """
    x = [0] * 21
    for s in SUB:
        r = target[s] // 2
        daftar = list(BUTIR[s])
        if cara in ('putar', 'isolasi'):
            g = k % 7
            daftar = daftar[g:] + daftar[:g]
        if cara == 'isolasi' and s == 'D':
            biasa = [i for i in daftar if i not in BUTIR_KRITIS]
            kritis = [i for i in daftar if i in BUTIR_KRITIS]
            langkah = [(i, 3) for i in biasa] + [(i, 2) for i in kritis] + [(i, 3) for i in kritis]
        else:
            langkah = [(i, 3) for i in daftar]
        for i, cap in langkah:
            if r == 0:
                break
            isi = min(cap - x[i - 1], r)
            x[i - 1] += isi
            r -= isi
        assert r == 0
    return x


# ------------------------------------------------------------ 3. rangkaian uji (nilai skor)
def satu_faktor(nilai_per_sub):
    """Ubah satu subskala, dua subskala lain ditahan pada 0 (Normal)."""
    kasus = []
    for s in SUB:
        for v in nilai_per_sub[s]:
            t = {u: 0 for u in SUB}; t[s] = v
            kasus.append(t)
    return kasus


def suite_ep():
    nilai = {}
    for s in SUB:
        b = BATAS[s]; pita = [(0, b[0] - 1), (b[0], b[1] - 1), (b[1], b[2] - 1),
                               (b[2], b[3] - 1), (b[3], 42)]
        rep = []
        for lo, hi in pita:
            g = [v for v in KISI if lo <= v <= hi]
            rep.append(g[len(g) // 2])
        nilai[s] = rep
    return nilai


def suite_naif():
    """BVA buku teks pada batas terbitan: c-1 dan c, ditambah 0 dan 42."""
    nilai = {}; tak_tercapai = 0; total = 0
    for s in SUB:
        cal = [0, 42]
        for c in BATAS[s]:
            cal += [c - 1, c]
        cal = sorted(set(cal)); total += len(cal)
        ok = [v for v in cal if v % 2 == 0]
        tak_tercapai += len(cal) - len(ok)
        nilai[s] = ok
    return nilai, total, tak_tercapai


def suite_kisi():
    """BVA sadar-kisi: nilai tercapai terbesar di pita bawah dan terkecil di pita atas."""
    nilai = {}
    for s in SUB:
        cal = {0, 42}
        for c in BATAS[s]:
            cal.add(max(v for v in KISI if v < c))
            cal.add(min(v for v in KISI if v >= c))
        nilai[s] = sorted(cal)
    return nilai


def suite_tuntas():
    return {s: list(KISI) for s in SUB}


# ------------------------------------------------------------ 4. analisis mutasi
def setara_pada_kisi(m):
    """Mutan setara bila keluarannya sama dengan acuan pada seluruh 22^3 tripel skor
    dan, untuk mutan pemetaan butir, pada sampel acak besar vektor butir."""
    if m.butir is BUTIR and m.faktor == 2 and m.butir_kritis == BUTIR_KRITIS \
            and m.butir_min == 3:
        for d, a, s, kr in itertools.product(KISI, KISI, KISI, (False, True)):
            if kr and d < 6:
                continue  # butir kritis bernilai 3 memaksa skor D minimal 6
            t = {'D': d, 'A': a, 'S': s}
            if m.dari_skor(t, kr) != ACUAN.dari_skor(t, kr):
                return False
        return True
    rnd = random.Random(7)
    for _ in range(200000):
        x = [rnd.randint(0, 3) for _ in range(21)]
        if m(x) != ACUAN(x):
            return False
    return True


def suite_butir():
    """Batas pada tingkat butir untuk aturan penanda: butir kritis bernilai 2 dan 3,
    butir lain 0, sehingga kategori Depresi tetap Normal."""
    out = []
    for i in BUTIR_KRITIS:
        for v in (2, 3):
            x = [0] * 21; x[i - 1] = v; out.append(x)
    return out


def suite_pelengkap():
    """Pelengkap keputusan untuk penanda F = C or I (gaya MC/DC):
    (C benar, I salah) dan (C salah, I salah) di sekitar batas Severe Depresi dengan
    konstruksi isolasi, ditambah batas tingkat butir untuk I."""
    out = suite_butir()
    for d in (20, 22):
        out.append(vektor({'D': d, 'A': 0, 'S': 0}, 'isolasi', 0))
    return out


def bangun(kasus_skor, cara):
    vs = [vektor(t, cara, k) for k, t in enumerate(kasus_skor)]
    for x, t in zip(vs, kasus_skor):
        assert ACUAN.skor(x) == t
    return vs


def jalankan(vektor_uji, daftar_mutan):
    harapan = [ACUAN(x) for x in vektor_uji]
    terbunuh = {}
    for kelas, m in daftar_mutan:
        mati = any(m(x) != h for x, h in zip(vektor_uji, harapan))
        terbunuh.setdefault(kelas, [0, 0])
        terbunuh[kelas][1] += 1
        if mati:
            terbunuh[kelas][0] += 1
    unik = len({tuple(x) for x in vektor_uji})
    return unik, terbunuh


def utama():
    tabel = periksa_tabel()
    semua = mutan()
    setara = [(k, m) for k, m in semua if setara_pada_kisi(m)]
    hidup = [(k, m) for k, m in semua if not setara_pada_kisi(m)]
    per_kelas = {}
    for k, m in semua:
        per_kelas.setdefault(k, [0, 0]); per_kelas[k][0] += 1
    for k, m in setara:
        per_kelas[k][1] += 1

    naif, naif_total, naif_tak = suite_naif()
    rangkaian = {
        'EP': suite_ep(),
        'BVA naif': naif,
        'BVA kisi': suite_kisi(),
        'Tuntas satu faktor': suite_tuntas(),
    }
    hasil = {}
    vb = suite_butir()
    vp = suite_pelengkap()
    for nama, nilai in rangkaian.items():
        kasus = satu_faktor(nilai)
        for cara, tambah in (('depan', None), ('putar', None), ('isolasi', None),
                             ('putar', 'butir'), ('depan', 'pelengkap'), ('putar', 'pelengkap')):
            vs = bangun(kasus, cara) + {'butir': vb, 'pelengkap': vp, None: []}[tambah]
            n, mati = jalankan(vs, hidup)
            tot_mati = sum(v[0] for v in mati.values())
            tot = sum(v[1] for v in mati.values())
            hasil['%s | %s%s' % (nama, cara, (' + ' + tambah) if tambah else '')] = dict(
                kasus=n, mutan_terbunuh=tot_mati, mutan_tak_setara=tot,
                skor_mutasi=round(100.0 * tot_mati / tot, 1),
                per_kelas={k: v for k, v in sorted(mati.items())},
                hidup=[m.nama for k, m in hidup
                       if not any(m(x) != ACUAN(x) for x in vs)])
    keluar = dict(
        tabel=tabel,
        mutan_total=len(semua), mutan_setara=len(setara),
        mutan_setara_nama=[m.nama for k, m in setara],
        per_kelas=per_kelas,
        naif=dict(total_nilai=naif_total, tak_tercapai=naif_tak),
        rangkaian={k: {s: v for s, v in r.items()} for k, r in rangkaian.items()},
        hasil=hasil,
    )
    return keluar


if __name__ == '__main__':
    out = utama()
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hasil.json')
    json.dump(out, open(p, 'w'), indent=1, ensure_ascii=False)
    print('mutan total', out['mutan_total'], '| setara', out['mutan_setara'])
    print('setara:', out['mutan_setara_nama'])
    print('per kelas [jumlah, setara]:', out['per_kelas'])
    print('BVA naif: nilai calon', out['naif']['total_nilai'], 'tak tercapai', out['naif']['tak_tercapai'])
    for s in SUB:
        t = out['tabel'][s]
        print('tabel', s, 'cakupan', t['cakupan_bulat'], 'tumpang', t['tumpang_tindih'],
              'titik genap per pita', t['titik_genap'], 'batas ganjil', t['batas_ganjil'])
    for k, v in out['hasil'].items():
        print('%-30s kasus %3d  skor mutasi %5.1f%%  (%d/%d)  %s' % (
            k, v['kasus'], v['skor_mutasi'], v['mutan_terbunuh'], v['mutan_tak_setara'],
            {kk: '%d/%d' % tuple(vv) for kk, vv in v['per_kelas'].items()}))
