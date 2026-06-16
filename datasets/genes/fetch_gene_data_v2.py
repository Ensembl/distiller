import csv
import argparse
import os
from datetime import timedelta
from time import perf_counter

import requests
from pymongo import MongoClient


METADATA_API_BASE_URL = "https://beta.ensembl.org/api/metadata"


def get_mongo_client():
    mongo_db_uri = os.getenv("MONGO_DB_URI")
    if not mongo_db_uri:
        raise RuntimeError("MONGO_DB_URI env variable is not set")
    return MongoClient(mongo_db_uri)


def is_latest_genome_uuid(genome_uuid):
    url = f"{METADATA_API_BASE_URL}/genome/{genome_uuid}/explain"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    genome_details = response.json()
    return genome_details.get("latest_genome") is None


def latest_genome_uuids_for_release_db(client, release_db):
    latest_genome_uuids = []
    genomes = client[release_db].genome.find({}).batch_size(1000)

    for genome in genomes:
        genome_uuid = genome["genome_id"]
        if is_latest_genome_uuid(genome_uuid):
            latest_genome_uuids.append(genome_uuid)
        else:
            print(f"Skipping non-latest genome_uuid: {genome_uuid}")

    return latest_genome_uuids


def write_header_row(writer):
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


def parse_gene_row(gene):
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
        gene.get("metadata", {}).get("name", {}).get("url", ""), # metadata_name_url
        gene.get("metadata", {}).get("name", {}).get("source", {}).get("id", ""), # metadata_name_source_id
        gene.get("metadata", {}).get("name", {}).get("source", {}).get("name", ""), # metadata_name_source_name
        gene.get("metadata", {}).get("name", {}).get("source", {}).get("description", ""), # metadata_name_source_description
        gene.get("metadata", {}).get("name", {}).get("source", {}).get("url", ""), # metadata_name_source_url
        gene.get("metadata", {}).get("name", {}).get("source", {}).get("release", ""), # metadata_name_source_release
        gene.get("slice", {}).get("region", {}).get("assembly", {}).get("accession_id", ""), # slice_region_assembly_accession_id
        gene.get("slice", {}).get("region", {}).get("assembly", {}).get("organism", {}).get("scientific_name", ""), # slice_region_assembly_organism_scientific_name
        gene.get("slice", {}).get("region", {}).get("assembly", {}).get("organism", {}).get("species", {}).get("taxon_id", ""), # slice_region_assembly_organism_species_taxon_id
        gene.get("slice", {}).get("region", {}).get("name", ""), # slice_region_name
        gene.get("slice", {}).get("region", {}).get("topology", ""), # slice_region_topology
        gene.get("slice", {}).get("region", {}).get("sequence", {}).get("checksum", ""), # slice_region_sequence_checksum
        gene.get("slice", {}).get("location", {}).get("end", ""), # slice_location_end
        gene.get("slice", {}).get("location", {}).get("length", ""), # slice_location_length
        gene.get("slice", {}).get("location", {}).get("start", ""), # slice_location_start
        gene.get("slice", {}).get("strand", {}).get("code", ""), # slice_strand_code
        gene.get("slice", {}).get("strand", {}).get("value", "") # slice_strand_value
    ]


def all_genome_ids_release_db_mapping():
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


def fetch_gene_data_for_all_release_dbs(latest_genomes_only=False):
    print("Fetching gene data for all release databases")

    release_dbs = []
    with get_mongo_client() as client:
        for name in client.list_database_names():
            if name.startswith("release_"):
                release_dbs.append(name)

    for release_db in release_dbs:
        fetch_gene_data_for_release_db(release_db, latest_genomes_only)


def fetch_gene_data_for_release_db(release_db, latest_genomes_only=False):
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

        for gene in genes:
            gene_row = parse_gene_row(gene)
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


def fetch_gene_data_for_genome_uuids(genome_uuids, latest_genomes_only=False):
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
            genes = client[release_db].gene.find(
                {"genome_id": genome_uuid}
            ).batch_size(batch_size)

            for gene in genes:
                gene_row = parse_gene_row(gene)
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
