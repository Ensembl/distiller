import appConfig from '../configs/app-config';

import type { Dataset, DatasetConfig } from '../types/dataset';
import type { TableColumn, TableData } from '../types/data-table';

export const fetchDatasets = async () => {
  const response = await fetch(`${appConfig.apiBaseUrl}/datasets`);
  if (!response.ok) {
    throw new Error(`Failed to fetch datasets: ${response.statusText}`);
  }

  const { datasets }: { datasets: Dataset[] } = await response.json();
  return datasets;
};

export const fetchDatasetConfig = async ({
  datasetId
}: {
  datasetId: string | number;
}) => {
  const response = await fetch(`${appConfig.apiBaseUrl}/dataset/${datasetId}/dataset-config`);
  if (!response.ok) {
    throw new Error(`Failed to fetch dataset config: ${response.statusText}`);
  }

  const datasetConfig: DatasetConfig = await response.json();
  return datasetConfig;
};

export const fetchRecords = async ({
  datasetId,
  columnIds,
  page,
  perPage
}: {
  datasetId: string;
  columnIds: TableColumn['id'][];
  page: number;
  perPage: number;
}) => {
  const response = await fetch(`${appConfig.apiBaseUrl}/dataset/${datasetId}/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      columns: columnIds,
      page,
      per_page: perPage
    })
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch records: ${response.statusText}`);
  }

  const tableData: TableData = await response.json();
  return tableData;
};
