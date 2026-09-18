import '../../components/filters/regex-filter';

import type { RegexFilter } from '../../types/filters';

export const Default = () => {
  const filterData: RegexFilter = {
    type: 'regex',
    id: 'my-match-filter',
    title: 'Hello world!',
    label: 'I am a label',
    example: '1:100-10000',
    regex: '[^:]+:\d+-\d+'
  };

  const wrapper = document.createElement('div');
  wrapper.classList.add('wrapper');
  const filterElement = document.createElement('ens-data-distiller-regex-filter');
  filterElement.filterData = filterData;
  wrapper.appendChild(filterElement);

  return wrapper;
};


export default {
  title: 'Filters/Regex filter'
};
