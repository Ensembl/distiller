import { mockDatasetsResponse, mockDatasetConfigResponse } from './mock-data';

export const fetchDatasets = async () => {
  return await Promise.resolve(mockDatasetsResponse);
};

export const fetchDatasetConfig = async ({
  datasetId
}: {
  datasetId: string | number;
}) => {
  return await Promise.resolve(mockDatasetConfigResponse);
};

export const fetchDatasetsAndFirstDatasetConfig = async() => {
  const { datasets } = await fetchDatasets();
  const firstDataset = datasets[0];
  const datasetConfig = await fetchDatasetConfig({
    datasetId: firstDataset.id
  });

  return {
    datasets,
    currentDatasetId: firstDataset.id,
    filterGroups: datasetConfig.filter_groups
  }
};