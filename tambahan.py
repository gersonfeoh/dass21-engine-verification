# -*- coding: utf-8 -*-
"""Pembanding konstruksi acak, analisis konflik gerbang-penanda, dan ekspor vektor uji."""
import csv, json, os, random, sys, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mesin import Mesin, mutan, BUTIR, BATAS, SUB, KATEGORI, BUTIR_KRITIS
import uji

ACUAN = Mesin()
semua = mutan()
hidup = [(k, m) for k, m in semua if not uji.setara_pada_kisi(m)]
dibangkitkan = 3 * 4 * 4
ambang = sum(1 for k, m in semua if k == 'M1 ambang')


def vektor_acak(target, rnd):
    x = [0] * 21
    for s in SUB:
        r = target[s] // 2
        while r > 0:
            i = rnd.choice(BUTIR[s])
            if x[i - 1] < 3:
                x[i - 1] += 1; r -= 1
    return x


kasus = []
for t in uji.satu_faktor(uji.suite_kisi()):
    if t not in kasus:
        kasus.append(t)
pel = uji.suite_pelengkap()
skor = []
for seed in range(100):
    rnd = random.Random(seed)
    vs = [vektor_acak(t, rnd) for t in kasus] + pel
    hs = [ACUAN(x) for x in vs]
    mati = sum(1 for k, m in hidup if any(m(x) != h for x, h in zip(vs, hs)))
    skor.append(100.0 * mati / len(hidup))
skor.sort()

# ---- konflik gerbang dan penanda: hitung tepat atas seluruh 4^21 vektor jawaban
def hitung(butir, syarat):
    """jumlah kombinasi nilai butir (0..3) yang memenuhi syarat(sum, ada_kritis3)"""
    n = 0
    for v in itertools.product(range(4), repeat=len(butir)):
        kr = any(val == 3 and i in BUTIR_KRITIS for i, val in zip(butir, v))
        if syarat(sum(v), kr):
            n += 1
    return n

bD = BUTIR['D']
d_normal_kritis = hitung(bD, lambda s, kr: 2 * s < 10 and kr)
d_normal = hitung(bD, lambda s, kr: 2 * s < 10)
d_flag = hitung(bD, lambda s, kr: 2 * s >= 21 or kr)
a_normal = hitung(BUTIR['A'], lambda s, kr: 2 * s < 8)
s_normal = hitung(BUTIR['S'], lambda s, kr: 2 * s < 15)
semua_vektor = 4 ** 21
gerbang_buka = d_normal * a_normal * s_normal
konflik = d_normal_kritis * a_normal * s_normal
ditandai = d_flag * 4 ** 14
ringkas = dict(
    acak_rerata=round(sum(skor) / len(skor), 1), acak_min=round(skor[0], 1),
    acak_maks=round(skor[-1], 1), acak_seratus_persen=sum(1 for s in skor if s == 100.0),
    ambang_dibangkitkan=dibangkitkan, ambang_valid=ambang,
    vektor_total=semua_vektor, gerbang_terbuka=gerbang_buka, konflik=konflik,
    konflik_persen_dari_gerbang=round(100.0 * konflik / gerbang_buka, 2),
    ditandai=ditandai, konflik_persen_dari_ditandai=round(100.0 * konflik / ditandai, 4),
    d_normal=d_normal, d_normal_kritis=d_normal_kritis,
)
print(ringkas)
json.dump(ringkas, open('hasil_tambahan.json', 'w'), indent=1)

# ---- ekspor vektor uji untuk mesin produksi (27 BVA kisi berotasi + 8 pelengkap)
with open('vektor_uji_bva_kisi_putar.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['kasus', 'kelompok', 'skor_D', 'skor_A', 'skor_S'] +
               ['b%02d' % i for i in range(1, 22)] +
               ['harapan_D', 'harapan_A', 'harapan_S', 'harapan_gerbang', 'harapan_penanda'])
    baris = []
    for k, t in enumerate(kasus):
        x = uji.vektor(t, 'putar', k)
        var = [s for s in SUB if t[s] != 0]
        baris.append(('BVA kisi ' + (var[0] if var else 'nol'), x))
    for x in pel:
        baris.append(('pelengkap keputusan', x))
    for n, (kel, x) in enumerate(baris, 1):
        h = ACUAN(x); sk = ACUAN.skor(x)
        w.writerow(['T%02d' % n, kel, sk['D'], sk['A'], sk['S']] + x +
                   [KATEGORI[h[0]], KATEGORI[h[1]], KATEGORI[h[2]],
                    'terbuka' if h[3] else 'tertutup', 'ya' if h[4] else 'tidak'])
print('vektor diekspor:', len(baris))
