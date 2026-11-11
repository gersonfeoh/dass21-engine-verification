# Conformance harness

`uji_konformansi.js` runs the unmodified scoring function `apiSubmitDass()` and eligibility function `_bolehChat()` of the screening platform against the 35-vector oracle `../vektor_uji_bva_kisi_putar.csv`.

The platform source (`Code.gs`, Google Apps Script) is **not** part of this repository. The harness takes its path as an argument.

## Requirements

Node.js 18 or later. No npm packages are needed.

## Usage

```
node konformansi/uji_konformansi.js /path/to/Code.gs
node konformansi/uji_konformansi.js /path/to/Code.gs --sensitivity
```

The harness prints the SHA-256 hash of the tested source file so that a result can be tied to one exact snapshot.

## Isolation

Every Apps Script service (`SpreadsheetApp`, `MailApp`, `PropertiesService`, and the others) is replaced by an inert stub. The I/O helpers `auth_`, `appendRow_`, `readAll_`, `catatEvent_` and `kirimEmailPenanda_` are replaced by in-memory versions. No spreadsheet row, crisis alert or e-mail is produced. The spreadsheet round trip between scoring and eligibility is emulated in memory.

## Sensitivity check

`--sensitivity` seeds two faults into an in-memory copy of the source: the upper bound of depression Normal is lowered from 9 to 7, and the check on item 21 is removed. Each fault must make exactly one oracle case fail.

## Expected output

For the snapshot reported in the paper:

```
Result: 35/35 passed
Cases that open the gate AND raise the flag: T29, T31, T33
Sensitivity [Depression Normal upper bound 9 -> 7]: 1 case(s) fail -> T02
Sensitivity [Item 21 check removed]: 1 case(s) fail -> T33
```

Category labels are mapped from the platform's Indonesian labels (Ringan, Sedang, Berat, Sangat Berat) to the oracle's English labels (Mild, Moderate, Severe, Extremely Severe).
