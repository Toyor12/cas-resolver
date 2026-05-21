# CAS Resolver

Processes CSV files containing chemical names and resolves each name to a
[CAS Registry Number](https://www.cas.org/cas-data/cas-registry) using the
[PubChem PUG REST API](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest).

## How it works

For each chemical name the tool calls:

```
GET https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/synonyms/JSON
```

It scans the returned synonym list for the first match of the CAS pattern
(`\d{2,7}-\d{2}-\d`) and writes it to the output file. Names that cannot be
resolved are recorded as `N/A`.

Requests are throttled to ≤ 4/s to stay within PubChem's published rate limit,
and transient failures are retried with exponential backoff (up to 3 retries).

## Requirements

Python 3.9 or later. No third-party packages — only the standard library is used.

## Installation

```bash
git clone https://github.com/Toyor12/cas-resolver.git
cd cas-resolver
```

## Usage

Place input CSV files in the `input/` directory. Each file must have a `Name`
column (additional columns are preserved as-is).

```
Name,"Quantity, kg"
Acetone,850
Ethanol,2200
```

Run the resolver:

```bash
python resolver.py
```

Output files are written to `output/` with the same filenames. A `cas_number`
column is appended to each row:

```
Name,"Quantity, kg",cas_number
Acetone,850,67-64-1
Ethanol,2200,64-17-5
```

### Custom directories

```bash
python resolver.py --input-dir /path/to/input --output-dir /path/to/output
```
