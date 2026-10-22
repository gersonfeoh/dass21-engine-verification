# -*- coding: utf-8 -*-
"""Gambar naskah CoreIT, hitam putih sesuai pedoman jurnal."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from mesin import BATAS, SUB

plt.rcParams.update({'font.family': 'Liberation Serif', 'font.size': 9,
                     'axes.linewidth': 0.6, 'savefig.dpi': 300})
OUT = os.path.dirname(os.path.abspath(__file__))
H = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hasil.json')))
NAMA = {'D': 'Depression', 'A': 'Anxiety', 'S': 'Stress'}
KAT = ['Normal', 'Mild', 'Moderate', 'Severe', 'Ext. severe']
ABU = ['#FFFFFF', '#E6E6E6', '#C8C8C8', '#A6A6A6', '#7F7F7F']


# ------------------------------------------------------------------ Gambar 1: alur riset
def alur():
    fig, ax = plt.subplots(figsize=(6.3, 2.2))
    ax.set_xlim(0, 100); ax.set_ylim(-2, 34); ax.axis('off')
    kotak = [
        (0.5, 'Scoring key,\nseverity bands,\ngate and flag rules', 'Specification'),
        (20.5, 'Reference\nengine and\npartition check', 'Implementation'),
        (40.5, 'Mutant\ngeneration in\nfive fault classes', 'Fault model'),
        (60.5, 'Test suites,\nconstructions and\ncomplement set', 'Test design'),
        (80.5, 'Mutation score\nand conformance\ntest', 'Evaluation'),
    ]
    for x, t, lab in kotak:
        ax.add_patch(FancyBboxPatch((x, 9), 18, 16, boxstyle='round,pad=0.3,rounding_size=1.4',
                                    fc='white', ec='black', lw=0.8))
        ax.text(x + 9, 17, t, ha='center', va='center', fontsize=7.6, linespacing=1.25)
        ax.text(x + 9, 30, lab, ha='center', va='center', fontsize=8, style='italic')
    for x in (18.8, 38.8, 58.8, 78.8):
        ax.annotate('', xy=(x + 1.6, 17), xytext=(x - 0.1, 17),
                    arrowprops=dict(arrowstyle='-|>', lw=0.8, color='black'))
    # umpan balik: turun dari kotak terakhir, menyusur di bawah, naik ke kotak pertama
    ax.plot([89.5, 89.5, 9.5, 9.5], [8.4, 3.5, 3.5, 7.6], color='black', lw=0.7, ls=(0, (3, 2)))
    ax.annotate('', xy=(9.5, 8.6), xytext=(9.5, 6.5),
                arrowprops=dict(arrowstyle='-|>', lw=0.7, color='black'))
    ax.text(50, 0.2, 'surviving mutants or failed conformance cases are traced back to the specification',
            ha='center', va='center', fontsize=7.3, style='italic')
    fig.savefig(os.path.join(OUT, 'fig1_flow.png'), bbox_inches='tight', pad_inches=0.03)
    plt.close(fig)


# ------------------------------------------------------------------ Gambar 2: kisi skor
def kisi():
    fig, axs = plt.subplots(3, 1, figsize=(6.3, 2.9), sharex=True)
    for ax, s in zip(axs, SUB):
        b = BATAS[s]; batas = [0] + list(b) + [43]
        for j in range(5):
            ax.add_patch(Rectangle((batas[j] - 0.5, -0.5), batas[j + 1] - batas[j], 1,
                                   fc=ABU[j], ec='black', lw=0.5))
            mid = (batas[j] - 0.5 + batas[j + 1] - 0.5) / 2
            ax.text(mid, 0.82, KAT[j], ha='center', va='bottom', fontsize=6.8)
        ax.scatter(range(0, 43, 2), [0] * 22, s=11, c='black', zorder=3)
        ax.scatter(range(1, 43, 2), [0] * 21, s=11, facecolors='white', edgecolors='black',
                   linewidths=0.5, zorder=3)
        for c in b:
            if c % 2 == 1:
                ax.annotate('', xy=(c - 0.5, -0.55), xytext=(c - 0.5, -1.15),
                            arrowprops=dict(arrowstyle='-|>', lw=0.6, color='black'))
        ax.set_ylim(-1.2, 1.55); ax.set_yticks([])
        ax.set_ylabel(NAMA[s], rotation=0, ha='right', va='center', fontsize=8.2)
        for sp in ('top', 'right', 'left'):
            ax.spines[sp].set_visible(False)
        if s != 'S':
            ax.spines['bottom'].set_visible(False)
            ax.tick_params(axis='x', bottom=False)
    axs[-1].set_xticks(range(0, 43, 2)); axs[-1].set_xlim(-1, 43)
    axs[-1].tick_params(axis='x', labelsize=7)
    axs[-1].set_xlabel('Doubled subscale score', fontsize=8.2)
    fig.text(0.99, 0.005, 'filled: attainable  |  open: unattainable  |  arrow: odd cut-point',
             ha='right', fontsize=7)
    fig.subplots_adjust(hspace=0.55, left=0.13, right=0.99, top=0.97, bottom=0.2)
    fig.savefig(os.path.join(OUT, 'fig2_lattice.png'))
    plt.close(fig)


# ------------------------------------------------------------------ Gambar 3: skor mutasi
def batang():
    suites = ['EP', 'BVA naif', 'BVA kisi', 'Tuntas satu faktor']
    label = ['Equivalence\npartitioning', 'Textbook\nBVA', 'Lattice-aware\nBVA', 'Exhaustive\nsingle-factor']
    seri = [(' | depan', 'Fixed construction', dict(color='white', hatch='////')),
            (' | putar', 'Rotating construction', dict(color='#BEBEBE')),
            (' | putar + pelengkap', 'Rotating + decision complement', dict(color='#3C3C3C'))]
    fig, ax = plt.subplots(figsize=(6.3, 2.7))
    x = list(range(len(suites))); w = 0.26
    for j, (suf, nama, gaya) in enumerate(seri):
        val = [H['hasil'][s + suf]['skor_mutasi'] for s in suites]
        bars = ax.bar([i + (j - 1) * w for i in x], val, w, edgecolor='black', lw=0.6,
                      label=nama, **gaya)
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 1.2, '%.1f' % r.get_height(),
                    ha='center', va='bottom', fontsize=6.6)
    n0 = [H['hasil'][s + ' | putar']['kasus'] for s in suites]
    n1 = [H['hasil'][s + ' | putar + pelengkap']['kasus'] for s in suites]
    ax.set_xticks(x)
    ax.set_xticklabels(['%s\n(%d / %d vectors)' % (l, a, b) for l, a, b in zip(label, n0, n1)],
                       fontsize=7.6)
    ax.set_ylabel('Mutation score (%)', fontsize=8.2); ax.set_ylim(0, 118)
    ax.set_yticks(range(0, 101, 20))
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=7.4, loc='upper left', ncol=3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig3_mutation.png'))
    plt.close(fig)


if __name__ == '__main__':
    alur(); kisi(); batang()
    print(sorted(os.listdir(OUT)))
