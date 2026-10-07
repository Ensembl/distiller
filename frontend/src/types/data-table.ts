export type TableColumn = {
  id: number | string;
  label: string;
  is_sortable: boolean;
  enable_by_default: boolean;
};

export type StringData = {
  style: 'string';
  value: string;
};

export type LinkData = {
  style: 'link';
  value: {
    label: string;
    url: string;
  };
};

export type TableCell = StringData | LinkData;

export type TableRow = Record<string, TableCell>;

export type TableData = {
  columns: Array<{
    id: number;
    name: string;
    label: string;
    style: TableCell['style'];
    sortable: boolean;
  }>;
  rows: TableRow[];
  meta: {
    total_hits: number;
    page: number;
    per_page: number;
  };
};
