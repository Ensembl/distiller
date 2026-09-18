import { mockDatasetsResponse, mockDatasetConfigResponse } from './mock-data';

export const fetchDatasets = async () => {
  const { datasets } = await Promise.resolve(mockDatasetsResponse);
  return datasets;
};

export const fetchDatasetConfig = async ({
  datasetId
}: {
  datasetId: string | number;
}) => {
  const datasetConfig = await Promise.resolve(mockDatasetConfigResponse);
  return datasetConfig;
};



/**

TODO: query the endpoint that returns the tabular data

The proposed payload (https://github.com/Ensembl/distiller/pull/6)


curl -X POST "http://localhost:8000/api/distiller/dataset/gene/records" \
  -H "Content-Type: application/json" \
  -d '{
    "columns":[1,2,5,6,8],
    "page":1,
    "per_page":100,
    "filters":[
      "filter_id":"gene_view_gene_symbol",
      "filter_value":"PPP2R2A"
    ],
    "order_by":{
      "column_id":1,
      "order":"DESC"
    }
  }'

 */


