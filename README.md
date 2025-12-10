## CIM-CGMES File Processing (_EQ_)
***

## Table of Contents
- [Description](#description) 
- [Background](#background)
- [Features](#features)
- [Layout](#layout) 
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Output](#output)
- [Contributing](#contributing)
- [License](#license)
- [References](#references)

---

## Description
This is a Python tool for automated parsing and processing of CIM CGMES EQ datasets.  
The script extracts all CIM classes from an EQ XML file inside a ZIP archive, converts each class into a structured CSV, and automatically enriches each CSV by resolving all rdf:resource references directly from the XML.

The tool reconstructs relationships between CIM objects using an internal ID index built from the original XML file.  
It supports any CGMES EQ profile that follows IEC 61970 conventions.

A second output is generated:
- Enriched CSVs (full CIM network object model with resolved relationships)  
- Clean Excel files (no IDs, no CIM resource pointers, no mRID values)

---

## Background
The Common Grid Model Exchange Specification (CGMES) defines how Transmission System Operators (TSOs) exchange power system models for operational and planning studies. It is based on the Common Information Model (CIM) and used in Europe under ENTSO-E requirements.

CGMES supports applications such as:
- Load flow and contingency analysis  
- Short circuit calculations  
- Market transparency and operational exchanges  
- Capacity allocation and congestion management  
- Security assessments  

Main CGMES file types:
- EQ  Equipment: physical network assets  
- SSH Steady State Hypothesis: operating setpoints  
- TP  Topology: electrical connections  
- SV  State Variables: load-flow solution  
- TPBD Topology Boundary  
- DL  Diagram Layout  
- GL  Geographical Layout  

This tool is designed for CIM files in general but has so far been tested only with EQ files.

---

## Features
The tool performs the following tasks:

- Reads an EQ XML file from inside a ZIP archive.  
- Extracts every CIM object containing rdf:ID.  
- Determines CIM class types using rdf:type where needed.  
- Builds a global identifier index for cross-object linking.  
- Detects every reference field ending in `__resource`.  
- Resolves these references by retrieving the target CIM object.  
- Enriches objects by attaching all attributes of referenced CIM objects.  
- Writes enriched CSV files to the output directory.  
- Writes clean Excel files (no IDs, no `__resource` columns, no mRID columns).  
- Works independently of CIM namespace version (CIM14, CIM15, CIM16).

Example – a line segment referencing a BaseVoltage object:

    ConductingEquipment.BaseVoltage__resource = "#_bv123"

becomes enriched with:

    ConductingEquipment.BaseVoltage__BaseVoltage.nominalVoltage
    ConductingEquipment.BaseVoltage__BaseVoltage.name
    ...

All extracted directly from the BaseVoltage object.

---

## Layout
Expected directory structure:

    project/
    │
    ├── your_EQ_file.zip                  (CGMES EQ ZIP archive)
    ├── cim_parser.py                     (main script)
    │
    └── OUTPUT/
          ├── eq_enriched/
          │     ├── ACLineSegment_enriched.csv
          │     ├── BaseVoltage_enriched.csv
          │     ├── Substation_enriched.csv
          │     └── ...
          │
          └── eq_clean/
                ├── ACLineSegment_clean.xlsx
                ├── BaseVoltage_clean.xlsx
                ├── Substation_clean.xlsx
                └── ...

Both `eq_enriched` and `eq_clean` directories are created automatically if they do not already exist.

---

## Prerequisites
- Python 3.12 or later  
- Recommended: Python virtual environment  

Required packages:

    pip install pandas openpyxl

No external APIs or internet access are required.

---

## Usage
1. Place your EQ ZIP file in the project directory.  
2. Update `zip_path`, `output_folder`, and `clean_output_folder` inside `cim_parser.py`.  
3. Run:

    python cim_parser.py

The script will:
- Read the XML inside the ZIP  
- Extract and index all CIM objects  
- Resolve all relationships (multiple passes to follow chains)  
- Write one enriched CSV per CIM class  
- Write one clean Excel file per CIM class (without IDs or CIM resource fields)

All main functions are documented with Python docstrings.

---

## Output

For each CIM class (for example BaseVoltage, ACLineSegment, BusbarSection), two outputs are created.

1. Enriched CSV  
   Contains:
   - Basic attributes directly from the CIM object  
   - All properties from child XML elements  
   - All resolved cross referenced attributes  

2. Clean Excel  
   Contains:
   - Only user-friendly attributes  
   - All ID-style columns removed (rdf_ID, any `@...`, all `__resource` fields)  
   - All mRID and *.mRID columns removed  

This provides:
- A full, machine-readable model (enriched CSV)  
- A human-friendly view for analysis and reporting (clean Excel)

---

## Contributing
Developed by:  
Anas Mufid Nurrochman  

Checked by (pending):  
Gregor Mathieson  

Contributions, suggestions, or improvements are welcome.  
Please keep docstrings and comments consistent with the existing style.

---

## License
This tool processes publicly defined CIM CGMES schemas.  
No proprietary APIs or paid services are used.

---

## References
- https://powsybl.readthedocs.io/projects/powsybl-core/en/stable/grid_exchange_formats/cgmes/  
- https://www.ofgem.gov.uk/decision/long-term-development-statement-direction  
- https://eepublicdownloads.entsoe.eu/clean-documents/CIM_documents/IOP/CGMES_2_5_TechnicalSpecification_61970-600_Part%201_Ed2.pdf  
