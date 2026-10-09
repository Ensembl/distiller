import csv
from _csv import Writer as CsvWriter
import argparse
import os
from datetime import timedelta
from functools import lru_cache
from time import perf_counter
from typing import Any

import requests
from pymongo import MongoClient
from pymongo.database import Database


# Ensembl metadata API is used in this script to check whether a genome is the latest one.
METADATA_API_BASE_URL = "https://ensembl.org/api/metadata"

# identifiers.org registry. Lists external databases (HGNC, RFAM, ...) with
# their home page, description and link pattern.
IDENTIFIERS_ORG_API_URL = "https://registry.api.identifiers.org/resolutionApi/getResolverDataset"

# Is this the right source ?
# Mapping file from the Thoas repo. Gives the identifiers.org name for each
# Ensembl source id, for example "HGNC" -> "hgnc".
XREF_MAPPING_URL = "https://raw.githubusercontent.com/Ensembl/ensembl-thoas/develop/docs/xref_LOD_mapping.json"

Document = dict[str, Any]
XrefSource = dict[str, str | None]
RegionDetails = dict[str, dict[str, Any]]


def get_mongo_client() -> MongoClient:
    mongo_db_uri = os.getenv("MONGO_DB_URI")
    if not mongo_db_uri:
        raise RuntimeError("MONGO_DB_URI env variable is not set")
    return MongoClient(mongo_db_uri)


def is_latest_genome_uuid(genome_uuid: str) -> bool:
    url = f"{METADATA_API_BASE_URL}/genome/{genome_uuid}/explain"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    genome_details = response.json()
    return genome_details.get("latest_genome") is None


def latest_genome_uuids_for_release_db(client: MongoClient, release_db: str) -> list[str]:
    latest_genome_uuids = []
    genomes = client[release_db].genome.find({}).batch_size(1000)

    for genome in genomes:
        genome_uuid = genome["genome_id"]
        if is_latest_genome_uuid(genome_uuid):
            latest_genome_uuids.append(genome_uuid)
        else:
            print(f"Skipping non-latest genome_uuid: {genome_uuid}")

    return latest_genome_uuids


def select_xref_url_pattern(resources: list[Document]) -> str | None:
    for resource in resources:
        if resource.get("official") is True:
            return resource.get("urlPattern")

    for resource in resources:
        if resource.get("deprecated") is False:
            return resource.get("urlPattern")

    return resources[0].get("urlPattern")


def select_source_resource(resources: list[Document]) -> Document:
    official_resources = [
        resource for resource in resources if resource.get("official") is True
    ]
    if official_resources:
        return official_resources[-1]
    return resources[0]


@lru_cache(maxsize=1)
def load_xref_sources() -> dict[str, XrefSource]:
    """
    Build a lookup of external sources (HGNC, RFAM, ...), keyed by the
    lower-case source id that genes use in MongoDB.

    For a gene's name source, MongoDB stores the id, name and release
    (for example "HGNC", "HGNC Symbol", "1") but not the link pattern, home
    page or description. Those come from two downloaded files: the Thoas
    mapping file, which gives the identifiers.org name of each Ensembl source,
    and the identifiers.org registry, which has the details for that name.

    The files are downloaded once per run; later calls reuse the result.

    Example:
        {
            "hgnc": {
                "namespace_prefix": "hgnc",
                "manual_xref_url": None,
                "url_pattern": "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/{$id}",
                "url": "https://www.genenames.org",
                "description": "HUGO Genome Nomenclature Committee"
            },
            ...
        }
    """
    mapping_response = requests.get(XREF_MAPPING_URL, timeout=30)
    mapping_response.raise_for_status()
    identifiers_org_response = requests.get(IDENTIFIERS_ORG_API_URL, timeout=60)
    identifiers_org_response.raise_for_status()

    namespaces = {
        namespace["prefix"]: namespace
        for namespace in identifiers_org_response.json()["payload"]["namespaces"]
    }

    xref_sources = {}
    for mapping in mapping_response.json()["mappings"]:
        source_id = mapping.get("ensembl_db_name", mapping["db_name"]).lower()
        namespace_prefix = mapping.get("id_namespace")
        resources = namespaces.get(namespace_prefix, {}).get("resources") or []

        xref_source = {
            "namespace_prefix": namespace_prefix,
            "manual_xref_url": mapping.get("manual_xref_url"),
            "url_pattern": None,
            "url": "",
            "description": ""
        }
        if resources:
            source_resource = select_source_resource(resources)
            xref_source["url_pattern"] = select_xref_url_pattern(resources)
            xref_source["url"] = source_resource.get("resourceHomeUrl", "")
            xref_source["description"] = source_resource.get("description", "")

        xref_sources[source_id] = xref_source

    return xref_sources


def xref_url_for_accession_id(accession_id: str | None, xref_source: XrefSource) -> str:
    """
    Build the URL of a gene's record in an external database such as
    HGNC, from the gene's accession id and that database's link pattern.
    Returns "" if the gene has no accession or the database has no link pattern.

    Example, for accession "HGNC:16848" and the "hgnc" source:
        "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:16848"

    Some patterns already end with the source name, such as ".../MGI:{$id}".
    The name is then removed from the accession.
    """
    if not accession_id:
        return ""

    namespace_prefix = xref_source.get("namespace_prefix")
    manual_xref_url = xref_source.get("manual_xref_url")
    if namespace_prefix is None and manual_xref_url:
        return manual_xref_url + accession_id

    url_pattern = xref_source.get("url_pattern")
    if namespace_prefix is None or not url_pattern:
        return ""

    url_pattern_tail = url_pattern.rsplit("/", 1)[-1]
    url_pattern_prefix = url_pattern_tail.split(":", 1)[0].lower() if ":" in url_pattern_tail else ""
    if (
        accession_id.lower().startswith(f"{namespace_prefix.lower()}:")
        and url_pattern_prefix == namespace_prefix.lower()
    ):
        accession_id = accession_id[len(namespace_prefix) + 1:]

    return url_pattern.replace("{$id}", accession_id)


def assembly_details_for_assembly_id(db: Database, assembly_id: str | None) -> Document:
    """
    Look up an assembly, then its organism, then its species.

    Example:
        {
            "assembly_accession_id": "GCA_000001405.29",
            "organism_scientific_name": "Homo sapiens",
            "species_taxon_id": 9606
        }
    """
    assembly = db.assembly.find_one({"assembly_id": assembly_id}) or {}
    organism = db.organism.find_one(
        {"organism_primary_key": assembly.get("organism_foreign_key")}
    ) or {}
    species = db.species.find_one(
        {"species_primary_key": organism.get("species_foreign_key")}
    ) or {}
    return {
        "assembly_accession_id": assembly.get("accession_id", ""),
        "organism_scientific_name": organism.get("scientific_name", ""),
        "species_taxon_id": species.get("taxon_id", "")
    }


def region_details_for_genome_uuid(db: Database, genome_uuid: str) -> RegionDetails:
    assembly_details = {}
    region_details = {}
    regions = db.region.find({"genome_id": genome_uuid}).batch_size(1000)

    for region in regions:
        assembly_id = region.get("assembly_id")
        if assembly_id not in assembly_details:
            assembly_details[assembly_id] = assembly_details_for_assembly_id(db, assembly_id)

        region_details[region["region_id"]] = {
            "name": region.get("name", ""),
            "topology": region.get("topology", ""),
            "sequence_checksum": region.get("sequence", {}).get("checksum", ""),
            **assembly_details[assembly_id]
        }

    return region_details


def write_header_row(writer: CsvWriter) -> None:
    writer.writerow([
        "symbol",
        "name",
        "alternative_symbols",
        "stable_id",
        "version",
        "unversioned_stable_id",
        "type",
        "so_term",
        "genome_uuid",
        "metadata_name_accession_id",
        "metadata_name_value",
        "metadata_name_url",
        "metadata_name_source_id",
        "metadata_name_source_name",
        "metadata_name_source_description",
        "metadata_name_source_url",
        "metadata_name_source_release",
        "slice_region_assembly_accession_id",
        "slice_region_assembly_organism_scientific_name",
        "slice_region_assembly_organism_species_taxon_id",
        "slice_region_name",
        "slice_region_topology",
        "slice_region_sequence_checksum",
        "slice_location_end",
        "slice_location_length",
        "slice_location_start",
        "slice_strand_code",
        "slice_strand_value"
    ])


def parse_gene_row(gene: Document, region_details: RegionDetails) -> list[Any]:
    region = region_details.get(gene.get("slice", {}).get("region_id"), {})
    name_metadata = gene.get("metadata", {}).get("name", {})
    name_source_id = name_metadata.get("source", {}).get("id") or ""
    name_source = load_xref_sources().get(name_source_id.lower(), {})

    return [
        gene.get("symbol", ""), # symbol
        gene.get("name", ""), # name
        gene.get("alternative_symbols", []), # alternative_symbols
        gene.get("stable_id", ""), # stable_id
        gene.get("version", ""), # version
        gene.get("unversioned_stable_id", ""), # unversioned_stable_id
        gene.get("type", ""), # type
        gene.get("so_term", ""), # so_term
        gene.get("genome_id", ""), # genome_uuid
        gene.get("metadata", {}).get("name", {}).get("accession_id", ""), # metadata_name_accession_id
        gene.get("metadata", {}).get("name", {}).get("value", ""), # metadata_name_value
        xref_url_for_accession_id(name_metadata.get("accession_id"), name_source), # metadata_name_url
        gene.get("metadata", {}).get("name", {}).get("source", {}).get("id", ""), # metadata_name_source_id
        gene.get("metadata", {}).get("name", {}).get("source", {}).get("name", ""), # metadata_name_source_name
        name_source.get("description", ""), # metadata_name_source_description
        name_source.get("url", ""), # metadata_name_source_url
        gene.get("metadata", {}).get("name", {}).get("source", {}).get("release", ""), # metadata_name_source_release
        region.get("assembly_accession_id", ""), # slice_region_assembly_accession_id
        region.get("organism_scientific_name", ""), # slice_region_assembly_organism_scientific_name
        region.get("species_taxon_id", ""), # slice_region_assembly_organism_species_taxon_id
        region.get("name", ""), # slice_region_name
        region.get("topology", ""), # slice_region_topology
        region.get("sequence_checksum", ""), # slice_region_sequence_checksum
        gene.get("slice", {}).get("location", {}).get("end", ""), # slice_location_end
        gene.get("slice", {}).get("location", {}).get("length", ""), # slice_location_length
        gene.get("slice", {}).get("location", {}).get("start", ""), # slice_location_start
        gene.get("slice", {}).get("strand", {}).get("code", ""), # slice_strand_code
        gene.get("slice", {}).get("strand", {}).get("value", "") # slice_strand_value
    ]


def all_genome_ids_release_db_mapping() -> dict[str, list[str]]:
    mapping = {}
    with get_mongo_client() as client:
        for name in client.list_database_names():
            if name.startswith("release_"):
                genomes = client[name].genome.find({}).batch_size(1000)
                for genome in genomes:
                    genome_id = genome["genome_id"]
                    if genome_id in mapping:
                        mapping[genome_id].append(name)
                    else:
                        mapping[genome_id] = [name]
    return mapping


def fetch_gene_data_for_all_release_dbs(latest_genomes_only: bool = False) -> None:
    print("Fetching gene data for all release databases")

    release_dbs = []
    with get_mongo_client() as client:
        for name in client.list_database_names():
            if name.startswith("release_"):
                release_dbs.append(name)

    for release_db in release_dbs:
        fetch_gene_data_for_release_db(release_db, latest_genomes_only)


def fetch_gene_data_for_release_db(release_db: str, latest_genomes_only: bool = False) -> None:
    print(f"Fetching gene data for release database: {release_db}")

    rows = []
    write_count = 0
    batch_size = 5_000
    output_file = f"{release_db}_genes.csv"

    with get_mongo_client() as client, open(
        output_file,
        "w",
        newline="",
        encoding="utf-8",
        buffering=1024 * 1024,
    ) as f:
        
        writer = csv.writer(f)
        write_header_row(writer)

        query = {}
        if latest_genomes_only:
            latest_genome_uuids = latest_genome_uuids_for_release_db(client, release_db)
            query = {"genome_id": {"$in": latest_genome_uuids}}

        genes = client[release_db].gene.find(query).batch_size(batch_size)
        region_details_by_genome_uuid = {}

        for gene in genes:
            genome_uuid = gene.get("genome_id")
            if genome_uuid not in region_details_by_genome_uuid:
                region_details_by_genome_uuid[genome_uuid] = region_details_for_genome_uuid(
                    client[release_db], genome_uuid
                )

            gene_row = parse_gene_row(gene, region_details_by_genome_uuid[genome_uuid])
            rows.append(gene_row)

            if len(rows) >= batch_size:
                writer.writerows(rows)
                write_count += len(rows)
                print(f"Added {write_count} rows to {output_file}")
                rows = []

        if rows:
            writer.writerows(rows)
            write_count += len(rows)
            print(f"Added {write_count} rows to {output_file}")

        print(f"Finished writing gene data for {release_db} to {output_file}")


def fetch_gene_data_for_genome_uuids(genome_uuids: list[str], latest_genomes_only: bool = False) -> None:
    print(f"Fetching gene data for genome uuids: {genome_uuids}")

    mapping = all_genome_ids_release_db_mapping()
    genome_uuid_release_dbs = []
    seen_genome_uuids = set()
    for genome_uuid in genome_uuids:
        if genome_uuid in seen_genome_uuids:
            continue
        seen_genome_uuids.add(genome_uuid)

        if latest_genomes_only and not is_latest_genome_uuid(genome_uuid):
            print(f"Skipping non-latest genome_uuid: {genome_uuid}")
            continue
        
        release_dbs = mapping.get(genome_uuid)
        if not release_dbs:
            print(f"No release database found for genome uuid: {genome_uuid}")
            continue

        for release_db in release_dbs:
            genome_uuid_release_dbs.append((genome_uuid, release_db))

    if not genome_uuid_release_dbs:
        print("No release databases found for any genome uuid")
        return

    rows = []
    write_count = 0
    batch_size = 5_000
    output_file = "genome_uuids_genes.csv"

    with get_mongo_client() as client, open(
        output_file,
        "w",
        newline="",
        encoding="utf-8",
        buffering=1024 * 1024,
    ) as f:
        
        writer = csv.writer(f)
        write_header_row(writer)

        for genome_uuid, release_db in genome_uuid_release_dbs:
            print(
                f"Fetching gene data for genome uuid: {genome_uuid} "
                f"from release database: {release_db}"
            )
            region_details = region_details_for_genome_uuid(client[release_db], genome_uuid)
            genes = client[release_db].gene.find(
                {"genome_id": genome_uuid}
            ).batch_size(batch_size)

            for gene in genes:
                gene_row = parse_gene_row(gene, region_details)
                rows.append(gene_row)

                if len(rows) >= batch_size:
                    writer.writerows(rows)
                    write_count += len(rows)
                    print(f"Added {write_count} rows to {output_file}")
                    rows = []

        if rows:
            writer.writerows(rows)
            write_count += len(rows)
            print(f"Added {write_count} rows to {output_file}")

    print(f"Finished writing gene data for genome uuids to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to create gene dataset from Ensembl MongoDB")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all_release_dbs", action="store_true", help="Gene data from all release databases")
    group.add_argument("--release_db", type=str, help="Gene data from a specific release database")
    group.add_argument("--genome_uuids", type=str, nargs="+", help="Gene data for a list of genome uuids")
    parser.add_argument("--latest_genomes_only", action="store_true", help="Only fetch gene data for latest genome uuids")
    args = parser.parse_args()

    started = perf_counter()

    if args.all_release_dbs:
        fetch_gene_data_for_all_release_dbs(args.latest_genomes_only)
    elif args.release_db:
        fetch_gene_data_for_release_db(args.release_db, args.latest_genomes_only)
    elif args.genome_uuids:
        fetch_gene_data_for_genome_uuids(args.genome_uuids, args.latest_genomes_only)
    else:
        print("No valid option provided. Use --help for more information.")

    elapsed = timedelta(seconds=round(perf_counter() - started))
    print(f"Total time: {elapsed}")
