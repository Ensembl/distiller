type SelectListFilterOption = {
  label: string;
  value: string;
};

type SelectListFilter = {
  id: string;
  type: 'checkbox_list',
  title: string;
  options: SelectListFilterOption[];
};

type SelectFilter = {
  id: string;
  type: 'text',
  title: string;
  label: string; // how to label the input box (textarea)
  hint?: string; // placeholder
  help?: string; // help text
};

type RegexFilter = {
  id: string;
  type: 'regex',
  title: string;
  fields: [
    {
      id: string;
      label: string;
      hint?: string;
      help?: string; // help text
      // validating_regex: string;
      // error_message: string;
    }
  ]
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
