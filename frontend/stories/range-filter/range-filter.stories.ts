import '../../components/filters/range-filter';

import type { RangeFilter } from '../../types/filters';

export const Default = () => {
  const filterData: RangeFilter = {
    type: 'range',
    id: 'my-range-filter',
    title: 'Hello world!',
    label: 'I am a label',
    min: 1,
    max: 100
  };

  const wrapper = document.createElement('div');
  wrapper.classList.add('wrapper');
  const filterElement = document.createElement('ens-data-distiller-range-filter');
  filterElement.filterData = filterData;
  wrapper.appendChild(filterElement);

  return wrapper;
};


export default {
  title: 'Filters/Range filter'
};
