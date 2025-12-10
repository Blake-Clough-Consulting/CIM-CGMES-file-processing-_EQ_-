"""
CIM CGMES EQ parser and enrichment script.

This module reads a CGMES EQ XML file from a ZIP archive, extracts all CIM
objects, builds an identifier index, resolves cross references between
objects, and writes one enriched CSV file per CIM class.

It also writes a cleaned Excel file per CIM class without ID or __resource
style columns into a separate folder.
"""

import os
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Tuple, Optional

import pandas as pd

# INPUTS
zip_path = r"C:\python\Pandapower\ukpn\LTDS_EPN_2025_02_EQ_2025-11-28_v1.0.zip"
output_folder = r"C:\python\Pandapower\ukpn\eq_enriched"
clean_output_folder = r"C:\python\Pandapower\ukpn\eq_clean"


def local_name(tag: str) -> str:
    """
    Extract the local XML tag name by removing the namespace.

    Parameters
    ----------
    tag : str
        Full XML tag including the namespace, for example '{ns}TagName'.

    Returns
    -------
    str
        Tag name without namespace, for example 'TagName'.
    """
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def get_rdf_attr(attrs: Dict[str, str], short_name: str) -> Optional[str]:
    """
    Retrieve an RDF attribute such as rdf:ID or rdf:resource.

    The function checks both namespace qualified attributes and plain
    attribute names, returning the first match.

    Parameters
    ----------
    attrs : dict of str to str
        Dictionary of XML attributes from an element.
    short_name : str
        Short attribute name without namespace, for example 'ID'
        or 'resource'.

    Returns
    -------
    str or None
        Attribute value if found, otherwise None.
    """
    for key, value in attrs.items():
        if key.endswith("}" + short_name) or key == short_name:
            return value
    return None


def canonical_id(value: Any) -> Optional[str]:
    """
    Normalise CIM identifier strings so rdf:ID and rdf:resource
    values can be matched consistently.

    The function removes combinations of leading '#', '#_', or '_' so that
    variations like '#_abc', '#abc', and '_abc' all become 'abc'.

    Parameters
    ----------
    value : Any
        Raw identifier value taken from an XML attribute. May be None
        or a non string type.

    Returns
    -------
    str or None
        Normalised identifier string, or None if the input is empty
        or missing.
    """
    if value is None or pd.isna(value):
        return None
    text = str(value)

    if text.startswith("#_"):
        text = text[2:]
    elif text.startswith("#"):
        text = text[1:]

    if text.startswith("_"):
        text = text[1:]

    return text


def parse_all_objects(
    root: ET.Element,
) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Dict[str, Any]]]:
    """
    Parse all CIM objects in the EQ XML and build an ID index.

    CIM objects are identified by the presence of rdf:ID.
    If an element is rdf:Description, the actual CIM class name is
    resolved via the child rdf:type/@rdf:resource.

    Parameters
    ----------
    root : xml.etree.ElementTree.Element
        Root element of the parsed EQ XML document.

    Returns
    -------
    records_by_type : dict
        Mapping from CIM class name to a list of object records. Each
        record is a flat dictionary of properties.
    id_index : dict
        Mapping from canonical CIM identifier to the corresponding
        record dictionary. This index is used for resolving references.
    """
    records_by_type: Dict[str, List[Dict[str, Any]]] = {}
    id_index: Dict[str, Dict[str, Any]] = {}

    for elem in root.iter():
        elem_local = local_name(elem.tag)

        rdf_id = get_rdf_attr(elem.attrib, "ID")
        if not rdf_id:
            continue

        eq_type = elem_local

        if elem_local == "Description":
            eq_type = None
            for child in elem:
                if local_name(child.tag) == "type":
                    res = get_rdf_attr(child.attrib, "resource")
                    if res:
                        eq_type = res.split("#")[-1]
                        break
            if eq_type is None:
                eq_type = "Description"

        record: Dict[str, Any] = {}
        record["xml_tag"] = elem_local
        record["rdf_ID"] = rdf_id

        # element attributes
        for attr_key, attr_value in elem.attrib.items():
            # skip ID attribute so we do not create redundant @ID
            if local_name(attr_key) == "ID":
                continue
            record["@" + local_name(attr_key)] = attr_value

        # child elements and attributes
        for child in elem:
            child_name = local_name(child.tag)
            text = (child.text or "").strip()

            if text:
                record[child_name] = text

            for attr_key, attr_value in child.attrib.items():
                col_name = f"{child_name}__{local_name(attr_key)}"
                record[col_name] = attr_value

        records_by_type.setdefault(eq_type, []).append(record)

        canonical = canonical_id(rdf_id)
        if canonical:
            id_index[canonical] = record

    records_by_type = {key: value for key, value in records_by_type.items() if value}
    return records_by_type, id_index


def resolve_references(
    records_by_type: Dict[str, List[Dict[str, Any]]],
    id_index: Dict[str, Dict[str, Any]],
) -> None:
    """
    Resolve all reference fields ending with '__resource' and enrich
    records with attributes from the referenced CIM objects.

    Parameters
    ----------
    records_by_type : dict
        Mapping from CIM class name to a list of object records. Records
        are modified in place.
    id_index : dict
        Mapping from canonical CIM identifier to the corresponding
        record dictionary.

    Returns
    -------
    None
        The function updates records_by_type in place.
    """
    for _, records in records_by_type.items():
        for record in records:
            resource_keys = [key for key in record.keys() if key.endswith("__resource")]

            for ref_key in resource_keys:
                ref_raw = record[ref_key]
                cid = canonical_id(ref_raw)
                if not cid:
                    continue

                target = id_index.get(cid)
                if target is None:
                    continue

                # avoid self reference
                if target is record:
                    continue

                prefix = ref_key.rsplit("__", 1)[0]

                # iterate over snapshot of target items to avoid dict size change issue
                for target_key, target_value in list(target.items()):
                    if target_key in ("xml_tag", "rdf_ID"):
                        continue

                    if target_value is None or (
                        isinstance(target_value, str) and target_value == ""
                    ):
                        continue

                    new_key = f"{prefix}__{target_key}"

                    if new_key not in record:
                        record[new_key] = target_value


def main() -> None:
    """
    Execute the full EQ parsing and enrichment workflow.

    Steps
    -----
    1. Ensure the output directories exist.
    2. Read the first XML file from the ZIP archive.
    3. Parse all CIM objects and build the identifier index.
    4. Resolve cross references between CIM objects multiple times
       so chained references are followed.
    5. Write enriched CSVs and cleaned Excel files per CIM class.
    """
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(clean_output_folder, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        xml_files = [name for name in zf.namelist() if name.lower().endswith(".xml")]
        if not xml_files:
            raise RuntimeError("No XML found in ZIP archive")
        xml_bytes = zf.read(xml_files[0])

    root = ET.fromstring(xml_bytes)

    records_by_type, id_index = parse_all_objects(root)

    if not records_by_type:
        print("No objects extracted")
        return

    max_reference_passes = 4
    for _ in range(max_reference_passes):
        resolve_references(records_by_type, id_index)

    for cim_type, records in records_by_type.items():
        df = pd.DataFrame(records)

        # write enriched CSV
        out_path = os.path.join(output_folder, f"{cim_type}_enriched.csv")
        df.to_csv(out_path, index=False, encoding="utf-8")
        print(f"Wrote {len(df)} rows -> {out_path}")

        # build clean version without IDs, __resource columns, and mRID columns
        df_clean = df.copy()

        cols_to_drop: List[str] = []

        # drop rdf_ID and any attribute style columns starting with '@'
        cols_to_drop.extend(
            [c for c in df_clean.columns if c == "rdf_ID" or c.startswith("@")]
        )

        # drop all reference columns
        cols_to_drop.extend(
            [c for c in df_clean.columns if c.endswith("__resource")]
        )

        # drop all mRID-related columns
        cols_to_drop.extend(
            [
                c
                for c in df_clean.columns
                if c.lower().endswith("mrid") or c.lower().endswith(".mrid")
            ]
        )

        # optional: drop xml_tag if not needed in clean views
        # cols_to_drop.append("xml_tag")

        df_clean = df_clean.drop(columns=list(set(cols_to_drop)), errors="ignore")

        clean_path = os.path.join(clean_output_folder, f"{cim_type}_clean.xlsx")
        df_clean.to_excel(clean_path, index=False)
        print(f"Wrote {len(df_clean)} rows -> {clean_path}")


if __name__ == "__main__":
    main()
