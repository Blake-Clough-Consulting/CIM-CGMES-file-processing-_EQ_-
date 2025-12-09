#Processs

import os
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd

# INPUTS
zip_path = r"C:\python\Pandapower\ukpn\LTDS_EPN_2025_02_EQ_2025-11-28_v1.0.zip"
output_folder = r"C:\python\Pandapower\ukpn\eq_enriched"


def local_name(tag: str) -> str:
    """Strip XML namespace: {ns}Tag -> Tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def get_rdf_attr(attrs: dict, short_name: str):
    """Get an RDF attribute like rdf:ID, rdf:about, rdf:resource."""
    for k, v in attrs.items():
        if k.endswith("}" + short_name) or k == short_name:
            return v
    return None


def canonical_id(value):
    """
    Normalise IDs and resources so they match:

    Examples:
      rdf:ID="_abc"            -> "abc"
      rdf:about="#_abc"        -> "abc"
      rdf:resource="#_abc"     -> "abc"
      rdf:resource="#abc"      -> "abc"
    """
    if value is None or pd.isna(value):
        return None
    v = str(value)

    # strip leading '#' and optional '_' after it
    if v.startswith("#_"):
        v = v[2:]
    elif v.startswith("#"):
        v = v[1:]

    # also strip leading '_' from IDs
    if v.startswith("_"):
        v = v[1:]

    return v


def parse_all_objects(root):
    """
    First pass: build records for all CIM objects and an ID index.

    Returns:
      records_by_type: dict[class_name] -> list[record dict]
      id_index: dict[canonical_id] -> record dict
    """
    records_by_type = {}
    id_index = {}

    for elem in root.iter():
        elem_local = local_name(elem.tag)

        # only consider elements that have rdf:ID or rdf:about
        rdf_id = get_rdf_attr(elem.attrib, "ID")
        rdf_about = get_rdf_attr(elem.attrib, "about")
        if not rdf_id and not rdf_about:
            continue

        # determine CIM class name
        eq_type = elem_local

        # if rdf:Description, resolve rdf:type to get the actual class
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

        rec = {}
        rec["xml_tag"] = elem_local
        rec["rdf_ID"] = rdf_id
        rec["rdf_about"] = rdf_about

        # element attributes
        for ak, av in elem.attrib.items():
            rec["@" + local_name(ak)] = av

        # child elements and attributes (properties)
        for child in elem:
            cname = local_name(child.tag)
            text = (child.text or "").strip()

            if text:
                rec[cname] = text

            for ak, av in child.attrib.items():
                col = f"{cname}__{local_name(ak)}"
                rec[col] = av

        # store by class
        records_by_type.setdefault(eq_type, []).append(rec)

        # index this object by a canonical ID
        cid = canonical_id(rdf_id) or canonical_id(rdf_about)
        if cid:
            # if duplicate cid happens, last one wins
            id_index[cid] = rec

    # drop empty classes
    records_by_type = {k: v for k, v in records_by_type.items() if v}
    return records_by_type, id_index


def resolve_references(records_by_type, id_index):
    """
    Second pass: for each record, follow *__resource values and
    copy in attributes from the referenced object.

    Example:
      ACLineSegment record has:
        ConductingEquipment.BaseVoltage__resource = "#_bv1"
      We:
        1. normalise "#_bv1" -> "bv1"
        2. look up that ID in id_index
        3. copy properties from the BaseVoltage record into this record.
    """
    for class_name, rec_list in records_by_type.items():
        for rec in rec_list:
            # find all reference-like fields
            resource_keys = [k for k in rec.keys() if k.endswith("__resource")]

            for rkey in resource_keys:
                ref_raw = rec[rkey]
                cid = canonical_id(ref_raw)
                if not cid:
                    continue

                target = id_index.get(cid)
                if target is None:
                    # reference to something not in EQ (maybe SSH, TP, etc.)
                    continue

                # prefix used for new columns to avoid collisions
                # e.g. "ConductingEquipment.BaseVoltage__resource"
                # -> "ConductingEquipment.BaseVoltage"
                prefix = rkey.rsplit("__", 1)[0]

                for tkey, tval in target.items():
                    # skip meta fields
                    if tkey in ("xml_tag", "rdf_ID", "rdf_about"):
                        continue

                    if tval is None or (isinstance(tval, str) and tval == ""):
                        continue

                    # new column name: prefix + "__" + target field
                    # Example:
                    #   prefix = "ConductingEquipment.BaseVoltage"
                    #   tkey   = "BaseVoltage.nominalVoltage"
                    #   new key = "ConductingEquipment.BaseVoltage__BaseVoltage.nominalVoltage"
                    new_key = f"{prefix}__{tkey}"

                    # do not overwrite if already present
                    if new_key not in rec:
                        rec[new_key] = tval


def main():
    os.makedirs(output_folder, exist_ok=True)

    # read XML inside ZIP
    with zipfile.ZipFile(zip_path, "r") as zf:
        xml_files = [n for n in zf.namelist() if n.lower().endswith(".xml")]
        if not xml_files:
            raise RuntimeError("No XML found in ZIP")
        xml_bytes = zf.read(xml_files[0])

    # parse XML
    root = ET.fromstring(xml_bytes)

    # first pass: collect all objects and build ID index
    records_by_type, id_index = parse_all_objects(root)

    if not records_by_type:
        print("No objects extracted")
        return

    # second pass: resolve references directly on records
    resolve_references(records_by_type, id_index)

    # write one CSV per CIM class
    for cim_type, records in records_by_type.items():
        df = pd.DataFrame(records)
        out_path = os.path.join(output_folder, f"{cim_type}_enriched.csv")
        df.to_csv(out_path, index=False, encoding="utf-8")
        print(f"Wrote {len(df)} rows -> {out_path}")


if __name__ == "__main__":
    main()
