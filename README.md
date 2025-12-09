## CIM-CGMES file-processing (_EQ_)
*** 
## Table of Contents

- [Description](#description) 
- [Features](#features)
- [Layout](#layout) 
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Output](#output)
- [Contributing](#contributing)
- [License](#license)
- [References](#references)

## Description
This is a Python tool for automated parsing and processing of CIM CGMES EQ datasets. The tool extracts all CIM classes from an EQ XML file contained inside a ZIP archive, converts each class into a structured CSV, and automatically enriches each CSV by resolving all rdf:resource references directly from the XML data.

## Background

The purpose of the Common Grid Model Exchange Specification (CGMES) is to define the interface between 
Transmission System Operators (TSO) software in order to exchange power system modelling information 
as required by the European Network of Transmission System Operators for Electricity (ENTSO-E) and TSO 
business processes.
The CGMES is used as a baseline exchange standard for the implementation of the Common Grid Model 
(CGM) methodologies in accordance with the requirements for the implementation of various European 
network codes and guidelines. The CGMES applies to applications dealing with power system data 
management, as well as applications supporting the following analyses: 
- load flow and contingency analyses, 
- short circuit calculations, 
- market information and transparency, 
- capacity calculation for capacity allocation and congestion management, and 
- dynamic security assessment. 
The conformity of the applications used for operational and system development exchanges with the CGMES 
is crucial for the needed interoperability of these applications. ENTSO-E therefore developed and approved 
the CGMES Conformity Assessment Framework as the guiding principles for assessing applications’ CGMES 
conformity. Based on those principles. This publicly available specification relies on the CGMES Conformity 
Assessment Process operated by ENTSO-E in order to ensure that the CGMES is properly implemented by 
suppliers of the applications used by TSOs.

The CGMES is defined using information on the Common Information Model (CIM) available in the public 
domain.

**Important Notes:**

There are a few different CIM file types, each covering a different layer of the network model (CIM-CGMES - powsybl-core v7.1.0):
- **EQ** (Equipment). Contains data that describes the equipment present in the network and its physical characteristics.
- **SSH** (Steady State Hypothesis). Required input parameters to perform power flow analysis, e.g., energy injections and consumptions and setpoint values for regulating controls.
- **TP**  (Topology). Describe how the equipment is electrically connected. Contains the definition of power flow buses.
- **SV** (State Variables). Contains all the information required to describe a steady-state power flow solution over the network.
- **TPBD** (Topology Boundary). Topology information associated with the boundary.
- **DL** (Diagram Layout): Diagram positions.
- **GL** (Geographical Layout):  Geographical positions.lol

**This script is has only been tested for the EQ file only**


It reconstructs relationships between CIM objects using an internal ID index built from the original XML file. 
This tool has been designed for engineering workflow automation and supports any CGMES EQ profile following IEC 61970 conventions.

## Features

The tool currently performs the following tasks:

- Automatically reads an EQ XML file from inside a ZIP archive.
- Extracts every CIM object with `rdf:ID` or `rdf:about`.
- Automatically resolves CIM class types from `rdf:type`.
- Creates one CSV file for each CIM class.
- Identifies all reference fields ending with `__resource`.
- Resolves these references by linking to the corresponding CIM object in the XML.
- Enriches the object by attaching all relevant attributes from the referenced class.
- Writes enriched CSVs to the output directory.
- Fully namespace agnostic: namespaces are normalized automatically.

**Example**
A line segment referencing a BaseVoltage object:

`ConductingEquipment.BaseVoltage__resource = "#_bv123"`


becomes enriched with:

```
ConductingEquipment.BaseVoltage__BaseVoltage.nominalVoltage
ConductingEquipment.BaseVoltage__BaseVoltage.name
...
```


All resolved directly from the BaseVoltage object in the XML.

## Layout

The directory structure is assumed to be:

```

project/
│
├── your_EQ_file.zip               (CGMES EQ ZIP archive)
├── cim_parser.py                  (your main parser script)
└── OUTPUT/\
     ├── ACLineSegment_enriched.csv
     ├── BaseVoltage_enriched.csv
     ├── Substation_enriched.csv
     └── ... more CIM class CSVs

```



If the OUTPUT directory does not exist, the tool will automatically create it.

All outputs are written into this directory.

## Prerequisites

This tool requires Python. Developed using Python version 3.12+.
It is recommended to use a virtual environment.

No external API calls are required.

## Usage

- Place your EQ ZIP file in the project directory.

- Update the zip_path and output_folder variables in the script.

- Run the script:

     `python cim_parser.py`

The script will:

- Read the XML inside the ZIP
- Extract all CIM objects
- Construct an ID index
- Resolve cross references
- Write enriched CSVs for every CIM class

All steps are explained with comments inside the script for clarity.

## Output

For each CIM class (such as BaseVoltage, ACLineSegment, BusbarSection), the tool produces:

1. A CSV file named:
<ClassName>_enriched.csv

2. Contains:
     - Basic attributes directly from the CIM object
     - All properties from child XML elements
     - All resolved cross referenced attributes

Example (ACLineSegment enriched):

```
rdf_ID
name
length
ConductingEquipment.BaseVoltage__resource
ConductingEquipment.BaseVoltage__BaseVoltage.nominalVoltage
ConductingEquipment.BaseVoltage__BaseVoltage.name
```


This gives you a single table containing both the object and all its referenced attributes.

## Contributing

Developed by
Anas Mufid Nurrochman

Checked by
Gregor Mathieson (not yet)

Contributions, suggestions, or improvements are welcome.
Please ensure that new functions follow the existing commenting style and maintain clarity for future users.

## License

This tool processes publicly defined CIM CGMES schemas.
No external proprietary APIs are used.

## References

https://powsybl.readthedocs.io/projects/powsybl-core/en/stable/grid_exchange_formats/cgmes/
https://www.ofgem.gov.uk/decision/long-term-development-statement-direction
https://eepublicdownloads.entsoe.eu/clean-documents/CIM_documents/IOP/CGMES_2_5_TechnicalSpecification_61970-600_Part%201_Ed2.pdf

