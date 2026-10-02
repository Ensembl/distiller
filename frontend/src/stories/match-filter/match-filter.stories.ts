import '../../components/filters/match-string-filter';

import type { MatchStringFilter } from '../../types/filters';

export const Default = () => {
  const filterData: MatchStringFilter = {
    type: 'match',
    id: 'my-match-filter',
    title: 'Hello world!',
    label: 'I am a label'
  };

  const wrapper = document.createElement('div');
  wrapper.classList.add('wrapper');
  const filterElement = document.createElement('ens-data-distiller-match-string-filter');
  filterElement.filterData = filterData;
  wrapper.appendChild(filterElement);

  return wrapper;
};


export default {
  title: 'Filters/Match filter'
};
