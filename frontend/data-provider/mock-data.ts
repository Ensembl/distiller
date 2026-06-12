import type { FilterGroup } from '../types/filters';

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
  filter_groups: FilterGroup[]
};