type SelectListFilterOption = {
  label: string;
  value: string;
  is_selected_by_default: boolean;
};


type SelectListFilter = {
  id: string;
  label: string;
  options: SelectListFilterOption[];
};

type Filter =
  | SelectListFilter;

type FilterGroup = {
  id: string; // not sure the client cares
  label: string;
  filters: Filter[];
};


type Dataset = {
  id: string;
  label: string;
};
