import type { FilterGroup } from '../types/filters';
import type { TableColumn } from '../types/data-table';

export const mockDatasetsResponse = {
  datasets: [
    { 
      label: "Genes",
      id: 'gene'
    },
    { 
      label: "Example",
      id: 'example'
    },
  ]
};


export const mockDatasetConfigResponse = {
  "columns": [
    {
      "id": 1,
      "label": "ID",
      "is_sortable": false,
      "enable_by_default": true
    },
    {
      "id": 2,
      "label": "Class",
      "is_sortable": true,
      "enable_by_default": true
    },
    {
      "id": 3,
      "label": "Stop",
      "is_sortable": true,
      "enable_by_default": true
    },
    {
      "id": 4,
      "label": "Start",
      "is_sortable": true,
      "enable_by_default": true
    },
    {
      "id": 7,
      "label": "Random",
      "is_sortable": true,
      "enable_by_default": true
    },
    {
      "id": 8,
      "label": "Region",
      "is_sortable": true,
      "enable_by_default": true
    },
    {
      "id": 9,
      "label": "Measurement",
      "is_sortable": false,
      "enable_by_default": true
    }
  ],
  "filter_groups": [
    {
      "id": "default",
      "label": "Filters",
      "filters": [
        {
          "id": "test_view_id",
          "title": "ID",
          "label": "ID",
          "type": "match"
        },
        {
          "id": "test_view_class",
          "title": "Class",
          "label": "Class",
          "type": "fixed_list",
          "options": [
            {
              "label": "class a",
              "value": "class A"
            },
            {
              "label": "class b",
              "value": "class B"
            }
          ]
        },
        {
          "id": "test_view_location",
          "title": "Location",
          "label": "Location",
          "type": "regex",
          "example": "1:100-10000",
          "regex": "(?P<region>[^:]+):(?P<start>\\d+)-(?P<end>\\d+)"
        }
      ]
    },
    {
      "id": "extras",
      "label": "Start",
      "filters": [
        {
          "id": "test_view_start",
          "title": "Start",
          "label": "Start",
          "type": "range",
          "min": 9,
          "max": 1001
        }
      ]
    }
  ]
} as {
  filter_groups: FilterGroup[],
  columns: TableColumn[]
};