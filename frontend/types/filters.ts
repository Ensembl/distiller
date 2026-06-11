// UI equivalent: a list of checkboxes
export type FixedListFilterOption = {
  label: string;
  value: string;
};

export type FixedListFilter = {
  type: 'fixed_list';
  id: string;
  title: string;
  options: FixedListFilterOption[];
};


// UI equivalent: an input of type text
export type MatchStringFilter = {
  type: 'match';
  id: string;
  title: string;
  label: string;
};

// UI equivalent: an input of type text, potentially with client-side validation
export type RegexFilter = {
  type: 'regex';
  id: string;
  title: string;
  label: string;
  example: string;
  regex: string;
};

export type RangeFilter = {
  type: 'range';
  id: string;
  title: string;
  label: string;
  min: number;
  max: number;
};

/**
 * Additional expected filters:
 * 'prefix' - same as MatchStringFilter, but results are matched by prefix search
 * 'user_list' - textarea in which user can enter multiple strings
 */

export type Filter =
  | FixedListFilter
  | MatchStringFilter
  | RegexFilter;


export type FilterGroup = {
  id: string;
  label: string;
  filters: Filter[];
};