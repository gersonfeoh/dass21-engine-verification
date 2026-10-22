# DASS-21 Engine Verification

Reference engine, mutant generator, test harness and test oracle for the article
*Lattice-Aware Boundary and Mutation Testing of a DASS-21 Screening and Triage Engine*.

All inputs are synthetic response vectors. No participant data are included.

## What is verified

| Output | Rule |
|---|---|
| Subscale score | `s_k = 2 * sum(x_i)` over the seven items of subscale k (0 to 42, even values only) |
| Severity category | Lovibond and Lovibond (1995) bands: D 10/14/21/28, A 8/10/15/20, S 15/19/26/34 |
| Eligibility gate G | open only when all three subscales are Normal |
| Needs-attention flag F | depression Severe or above, OR item 10, 17 or 21 rated 3 |

## Files

| File | Content |
|---|---|
| `mesin.py` | parameterised reference engine and 105 first-order mutants in five classes |
| `uji.py` | partition check, test suites (EP, textbook BVA, lattice-aware BVA, exhaustive single-factor), item-vector constructions, decision complement, mutation analysis; writes `hasil.json` |
| `tambahan.py` | random-construction robustness check, exact gate and flag conflict count, export of the test oracle; writes `hasil_tambahan.json` and `vektor_uji_bva_kisi_putar.csv` |
| `gambar.py` | Figures 1 to 3 of the article |
| `vektor_uji_bva_kisi_putar.csv` | the 35-vector test oracle (27 lattice-aware BVA vectors with rotating construction and 8 decision-complement vectors) with expected outputs |

Identifiers and column names are in Indonesian. Key terms: *butir* item, *batas* cut-point,
*gerbang* gate, *penanda* flag, *harapan* expected value, *terbuka/tertutup* open/closed,
*ya/tidak* yes/no, *mutan setara* equivalent mutant.

## Reproduce

```
pip install -r requirements.txt
python uji.py
python tambahan.py
python gambar.py
```

Runtime is a few seconds. Results are deterministic (random checks use fixed seeds).

## Main results

- 105 mutants, 12 equivalent (one per cut-point), 93 non-equivalent.
- 12 of 30 textbook boundary values are unattainable because subscale scores are even.
- Lattice-aware BVA with rotating construction plus the decision complement kills 93/93 mutants with 35 vectors; the exhaustive single-factor suite needs 71.
- Under the documented rules, 6.5% of response vectors that open the gate also raise the flag.

## Using the oracle on another implementation

Feed columns `b01` to `b21` of each row to the implementation under test and compare its
three categories, gate decision and flag with columns `harapan_D` to `harapan_penanda`.
Run it against an isolated copy, not against a deployment that stores results.

## License

MIT. See `LICENSE`.
