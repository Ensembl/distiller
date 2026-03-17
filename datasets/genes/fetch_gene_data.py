import requests 
import csv
import pandas

results_file = "example_genes.tsv"
input_data_file = "genomes_and_genes.csv"
thoas_url = "https://beta.ensembl.org/data/graphql"

# NB: This only works for genes with symbols, and is only suitable for generating some test data.

def get_gene_data(genome_id: str, symbol: str):  
    variables = {
        "genomeId": genome_id,
        "symbol": symbol
    }

    query = """
        query GetGene($genomeId: String!, $symbol: String!) {
            genes(
                by_symbol: {genome_id: $genomeId, symbol: $symbol}
            ) {
                symbol
                name
                alternative_symbols
                stable_id
                version
                unversioned_stable_id
                type
                metadata {
                name {
                    accession_id
                    value
                    url
                    source {
                    id
                    name
                    description
                    url
                    release
                    }
                }
                }
                slice {
                region {
                    assembly {
                    accession_id
                    organism {
                        scientific_name
                        species {
                        taxon_id
                        }
                    }
                    }
                    name
                    topology
                    sequence {
                    checksum
                    }
                }
                location {
                    end
                    length
                    start
                }
                strand {
                    code
                    value
                }
                }
                so_term
            }
        }
        """

    try:
        response = requests.post(
            thoas_url,
            json={
                "query": query,
                "variables": variables
            },
            headers={"Content-Type": "application/json"},
            timeout=100
        )

        data = response.json()
        for gene in data["data"]["genes"]:
            gene["genome_uuid"] = genome_id
        
        return data["data"]["genes"]

    except Exception as e:
        print("Request failed:", e)

def get_data_for_genomes_and_genes(genomes_and_genes_list_file):
    with open(genomes_and_genes_list_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)  # reads rows as dictionaries
        for row in reader:
            genome_id = row["genome_id"].strip()
            symbol = row["symbol"].strip()
            print(genome_id, " : ", symbol)
            graphql_data = get_gene_data(genome_id, symbol)
            format_line(graphql_data, genome_id)

def write_line(df):
    df.to_csv(results_file, mode='a', index=False, header=False, sep="\t")


def format_line(data, genome_id):
    write_line(pandas.json_normalize(data))
    
def setup_file(filename):
    with open(filename, "w") as f:
        f.write("symbol\tname\talternative_symbols\tstable_id\tversion\tunversioned_stable_id\ttype\tso_term\tgenome_uuid\tmetadata_name_accession_id\tmetadata_name_value\tmetadata_name_url\tmetadata_name_source_id\tmetadata_name_source_name\tmetadata_name_source_description\tmetadata_name_source_url\tmetadata_name_source_release\tslice_region_assembly_accession_id\tslice_region_assembly_organism_scientific_name\tslice_region_assembly_organism_species_taxon_id\tslice_region_name\tslice_region_topology\tslice_region_sequence_checksum\tslice_location_end\tslice_location_length\tslice_location_start\tslice_strand_code\tslice_strand_value\n")

print("Writing header...")
setup_file(results_file)
print("Fetching and writing data")
get_data_for_genomes_and_genes(input_data_file)
print("All done.")    