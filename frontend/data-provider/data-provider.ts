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