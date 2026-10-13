import type { Dataset, DatasetConfig } from '../types/dataset';
import type { OrderBy, TableColumn, TableData } from '../types/data-table';

export const fetchDatasets = async ({
  apiBaseUrl
}: {
  apiBaseUrl: string;
}) => {
  const response = await fetch(`${apiBaseUrl}/datasets`);
  if (!response.ok) {
    throw new Error(`Failed to fetch datasets: ${response.statusText}`);
  }

  const { datasets }: { datasets: Dataset[] } = await response.json();
  return datasets;
};

export const fetchDatasetConfig = async ({
  apiBaseUrl,
  datasetId
}: {
  apiBaseUrl: string;
  datasetId: string | number;
}) => {
  const response = await fetch(`${apiBaseUrl}/dataset/${datasetId}/dataset-config`);
  if (!response.ok) {
    throw new Error(`Failed to fetch dataset config: ${response.statusText}`);
  }

  const datasetConfig: DatasetConfig = await response.json();
  return datasetConfig;
};

export const fetchRecords = async ({
  apiBaseUrl,
  datasetId,
  columnIds,
  page,
  perPage,
  orderBy
}: {
  apiBaseUrl: string;
  datasetId: string;
  columnIds: TableColumn['id'][];
  page: number;
  perPage: number;
  orderBy: OrderBy | null;
}) => {
  const orderByPayload = orderBy
    ? { column_id: orderBy.columnId, order: orderBy.order.toUpperCase() }
    : null;

  const response = await fetch(`${apiBaseUrl}/dataset/${datasetId}/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      columns: columnIds,
      page,
      per_page: perPage,
      order_by: orderByPayload
    })
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch records: ${response.statusText}`);
  }

  const tableData: TableData = await response.json();
  return tableData;
};
