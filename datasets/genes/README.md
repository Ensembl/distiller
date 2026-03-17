# Gene Mapping

## Thoas query

```json

query MyQuery {
  genes(
    by_symbol: {genome_id: "2b5fb047-5992-4dfb-b2fa-1fb4e18d1abb", symbol: "BRCA2"}
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

```


## Example response

```json
{
  "data": {
    "genes": [
      {
        "symbol": "BRCA2",
        "name": "BRCA2 DNA repair associated",
        "alternative_symbols": [
          "BRCC2",
          "FACD",
          "FAD",
          "FAD1",
          "FANCD",
          "FANCD1",
          "XRCC11"
        ],
        "stable_id": "ENSG00000139618.19",
        "version": 19,
        "unversioned_stable_id": "ENSG00000139618",
        "type": "Gene",
        "metadata": {
          "name": {
            "accession_id": "HGNC:1101",
            "value": "BRCA2 DNA repair associated",
            "url": "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:1101",
            "source": {
              "id": "HGNC",
              "name": "HGNC Symbol",
              "description": "HUGO Genome Nomenclature Committee",
              "url": "https://www.genenames.org",
              "release": "1"
            }
          }
        },
        "slice": {
          "region": {
            "assembly": {
              "accession_id": "GCA_000001405.29",
              "organism": {
                "scientific_name": "Homo sapiens",
                "species": {
                  "taxon_id": 9606
                }
              }
            },
            "name": "13",
            "topology": "linear",
            "sequence": {
              "checksum": "17dab79b963ccd8e7377cef59a54fe1c"
            }
          },
          "location": {
            "end": 32400268,
            "length": 85183,
            "start": 32315086
          },
          "strand": {
            "code": "forward",
            "value": 1
          }
        },
        "so_term": "protein_coding"
      }
    ]
  },
  "extensions": {
    "execution_time_in_seconds": 0.21
  }
}
```

For each gene returned:


| column_name                           |  Thoas_location                                                           |
|---------------------------------------|---------------------------------------------------------------------------|
| genome_uuid                           |  genome_uuid                                                              |
| assembly_accession                    |  gene["slice"]["region"]["assembly"]["accession_id"]                      |
| gene_symbol                           |  gene["symbol"]                                                           |
| gene_name                             |  gene["name"]                                                             |
| so_term                               |  gene["so_term"]                                                          |
| species_scientific_name               |  gene["slice"]["region"]["assembly"]["organism"]["scientific_name"]       |
| species_taxon_id                      |  gene["slice"]["region"]["assembly"]["organism"]["species"]["taxon_id"]   |
| gene_alternative_symbols              |  gene["alternative_symbols"]                                              |
| gene_stable_id                        |  gene["stable_id"]                                                        |
| gene_version                          |  gene["version"]                                                          |
| gene_unversioned_stable_id            |  gene["unversioned_stable_id"]                                            |
| type                                  |  gene["type"]                                                             |
| gene_name_metadata_accession_id       |  gene["metadata"]["name"]["accession_id"]                                 |
| gene_name_metadata_value              |  gene["metadata"]["name"]["value"]                                        |
| gene_name_metadata_url                |  gene["metadata"]["name"]["url"]                                          |
| gene_name_metadata_source_id          |  gene["metadata"]["name"]["source"]["id"]                                 |
| gene_name_metadata_source_name        |  gene["metadata"]["name"]["source"]["name"]                               |
| gene_name_metadata_source_description |  gene["metadata"]["name"]["source"]["description"]                        |
| gene_name_metadata_source_url         |  gene["metadata"]["name"]["source"]["url"]                                |
| gene_name_metadata_source_release     |  gene["metadata"]["name"]["source"]["release"]                            |
| slice_region_name                     |  gene["slice"]["region"]["name"]                                          |
| slice_region_topology                 |  gene["slice"]["region"]["topology"]                                      |
| slice_region_sequence_checksum        |  gene["slice"]["region"]["sequence"]["checksum"]                          |
| slice_location_start                  |  gene["slice"]["location"]["start"]                                       |
| slice_location_end                    |  gene["slice"]["location"]["end"]                                         |
| slice_location_length                 |  gene["slice"]["location"]["length"]                                      |
| slice_strand_code                     |  gene["slice"]["strand"]["code"]                                          |
| slice_strand_value                    |  gene["slice"]["strand"]["value"]                                         |        

