export type TableColumn = {
  id: number | string;
  label: string;
  is_sortable: boolean;
  enable_by_default: boolean;
};

export type StringData = {
  type: 'string';
  column_id: string;
  value: string | null;
};

export type LinkData = {
  type: 'link';
  column_id: string;
  value: string | null;
  url: string | null;
};

export type LinkArrayData = {
  type: 'link-array';
  column_id: string;
  values: Array<{
    value: string;
    url: string | null;
  }>;
};
