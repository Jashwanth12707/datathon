# KSP Synthetic Crime Data Generator

Production-oriented Python project for generating realistic relational crime datasets for a Karnataka State Police AI Hackathon.

The project generates CSV files suitable for PostgreSQL imports, Neo4j/graph loading, RAG indexing, dashboards, geospatial heatmaps, crime analytics, and ML experiments. It writes rows incrementally, so large FIR volumes can be generated without keeping complete datasets in RAM.

The project also includes a Catalyst bulk-loader so the generated CSVs can be moved into Catalyst Data Store through File Store backed bulk write jobs.

## Files Generated

| CSV | Purpose |
| --- | --- |
| `fir.csv` | FIR master table with crime, legal section, station, complainant, location, and status fields |
| `victim.csv` | Victims linked to valid FIR IDs |
| `accused.csv` | Accused persons linked to valid FIR IDs, with repeat offender and gang attributes |
| `court_case.csv` | Court proceedings linked to FIR IDs |
| `officer.csv` | KSP officer master data |
| `station.csv` | Police station master data |
| `bond.csv` | Bonds linked to FIR and accused IDs |
| `vehicle.csv` | Vehicles linked to FIRs where applicable |
| `evidence.csv` | Evidence records linked to FIRs and collecting officers |
| `witness.csv` | Witness statements linked to FIRs |
| `cctv.csv` | Camera registry with geospatial coordinates and FIR linkage |
| `location.csv` | Karnataka district, taluk, ward/village, station, and coordinate lookup |
| `criminal_network.csv` | Accused-to-accused graph edges for Neo4j/network analysis |
| `history_sheet.csv` | History sheet records linked to accused IDs |
| `gang.csv` | Gang master records used by accused and graph outputs |
| `_manifest.json` | Generation counts, columns, seed, and elapsed time |

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install zcatalyst-sdk==1.4.0
```

On macOS/Linux, activate with `source .venv/bin/activate`.

## Generate Data

Tiny smoke dataset:

```bash
python generate.py --small
```

Default production-style dataset:

```bash
python generate.py
```

Custom output directory:

```bash
python generate.py --output-dir D:\ksp-output
```

Scale all configured counts:

```bash
python generate.py --scale 10
```

Override specific counts:

```bash
python generate.py --fir 1000000 --victim 850000 --accused 300000 --evidence 2000000
```

Environment variable overrides are also supported:

```bash
set KSP_FIR_COUNT=1000000
set KSP_OUTPUT_DIR=D:\ksp-output
python generate.py
```

## Default Volumes

Defaults are set in `config.py`:

| Entity | Rows |
| --- | ---: |
| FIR | 100,000 |
| Victim | 85,000 |
| Accused | 30,000 |
| Evidence | 200,000 |
| Witness | 120,000 |
| Court cases | 40,000 |
| Vehicle | 50,000 |
| CCTV cameras | 10,000 |
| Officer | 8,000 |
| Station/location | 420 |
| Bond | 25,000 |
| Gang | 450 |
| History sheet | 18,000 |
| Criminal network edges | 60,000 |

## Realism Features

The generator models practical crime-data patterns:

- Vehicle theft occurs mostly at night.
- Cyber fraud is weighted toward working hours.
- Chain snatching appears around morning and evening movement windows.
- Domestic violence is weighted toward night hours.
- Festival months create crowd-crime spikes.
- Election months increase election-violence records.
- Monsoon months increase road accident probability.
- Accused generation includes repeat profiles, aliases, wanted status, gang membership, and history-sheeter flags.
- Criminal network edges use `networkx` to create a realistic connected associate graph.
- Coordinates are jittered around real Karnataka district/taluk/place anchors.
- All dependent rows reference deterministic valid IDs.

## PostgreSQL Import Notes

All CSVs use UTF-8 with a header row and plain scalar values. Recommended import pattern:

```sql
\copy fir FROM 'output/fir.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
```

Load master tables first:

1. `location.csv`
2. `station.csv`
3. `officer.csv`
4. `gang.csv`
5. `fir.csv`
6. dependent tables such as `victim.csv`, `accused.csv`, `evidence.csv`, `court_case.csv`
7. graph/history tables

## Neo4j Loading Ideas

Use `criminal_network.csv` as relationship data:

```cypher
LOAD CSV WITH HEADERS FROM 'file:///criminal_network.csv' AS row
MERGE (a:Accused {accused_id: row.source_accused_id})
MERGE (b:Accused {accused_id: row.target_accused_id})
MERGE (a)-[:ASSOCIATED_WITH {
  edge_id: row.edge_id,
  relationship: row.relationship,
  gang_id: row.gang_id,
  strength: toFloat(row.strength),
  first_seen_fir: row.first_seen_fir
}]->(b);
```

## Catalyst Data Store Workflow

Use this when you want the synthetic data inside your Catalyst project.

1. Create Catalyst Data Store tables matching [catalyst_schema.json](/D:/datathon/ksp-data-generator/catalyst_schema.json).
2. Create one Catalyst File Store folder and note its folder ID.
3. Generate CSVs with `python generate.py --output-dir .\output`.
4. Set Catalyst credentials and project metadata in your shell.
5. Run the bulk-loader to upload CSVs and trigger Data Store imports in dependency order.

### Required Environment

The loader uses the Catalyst Python SDK outside a function, so it expects:

- `CATALYST_AUTH`: JSON string containing a valid Catalyst credential object. The SDK accepts `refresh_token`, `access_token`, or `ticket`.
- `CATALYST_PROJECT_ID`
- `CATALYST_PROJECT_KEY`
- `CATALYST_PROJECT_DOMAIN`
- `CATALYST_ENVIRONMENT` optional, defaults to `Development`

Example PowerShell session:

```powershell
$env:CATALYST_AUTH='{"refresh_token":"<token>","client_id":"<client-id>","client_secret":"<client-secret>"}'
$env:CATALYST_PROJECT_ID='1234567890001'
$env:CATALYST_PROJECT_KEY='1234567890001'
$env:CATALYST_PROJECT_DOMAIN='https://your-project.zohocatalyst.com'
$env:CATALYST_ENVIRONMENT='Development'
```

### Bulk Load Command

```powershell
python catalyst_datastore_loader.py `
  --csv-dir .\output `
  --filestore-folder-id 24071000000032001 `
  --operation insert
```

For partial loads:

```powershell
python catalyst_datastore_loader.py `
  --csv-dir .\output `
  --filestore-folder-id 24071000000032001 `
  --only location station officer gang fir
```

### Recommended Table Types

These column choices keep imports predictable in Catalyst:

- IDs and FK-like references: `text`
- Names, addresses, acts, sections, descriptions, status fields: `text`
- `year`, `age`, `member_count_estimate`, `coverage_angle`, `bond_amount`, `fir_count`, `risk_score`: `bigint` or `number`
- `latitude`, `longitude`, `strength`: `decimal`
- `date`, `occurrence_date`, `statement_date`, `charge_sheet_date`, `hearing_date`, `collection_date`, `execution_date`, `expiry_date`, `opened_on`, `last_reviewed`: `date`
- `time`, `occurrence_time`: `text`
- booleans such as `statement_recorded`, `history_sheeter`, `wanted`, `active`: `boolean` if your Catalyst table setup supports direct CSV boolean parsing, otherwise keep them as `text`

### Load Order

The loader imports tables in this order so dependent data lands after its parents:

`location -> station -> officer -> gang -> fir -> victim -> accused -> evidence -> witness -> court_case -> vehicle -> cctv -> bond -> history_sheet -> criminal_network`

### Notes

- Catalyst Data Store table creation is not exposed in the Python SDK, so table creation still needs to happen in Catalyst first.
- For million-row scale, prefer Catalyst bulk write rather than row-by-row inserts.
- If you want idempotent reloads, create unique keys in Catalyst and use `--operation upsert`.

## Project Structure

```text
ksp-data-generator/
  config.py
  generate.py
  requirements.txt
  README.md
  generators/
    fir_generator.py
    victim_generator.py
    accused_generator.py
    officer_generator.py
    station_generator.py
    court_generator.py
    bond_generator.py
    vehicle_generator.py
    witness_generator.py
    evidence_generator.py
    cctv_generator.py
    location_generator.py
    gang_generator.py
    history_generator.py
    network_generator.py
    utils.py
```
