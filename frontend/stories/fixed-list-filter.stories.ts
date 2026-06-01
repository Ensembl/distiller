import '../components/filters/fixed-list-filter';

import type { FixedListFilter } from '../types/filters';

import './fixed-list-filter.stories.css';

const lipsum = `
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Vivamus faucibus sapien neque, eget mollis ligula malesuada sit amet.
Cras et aliquam ante, placerat mollis odio.
Curabitur dictum massa quis ipsum placerat, ac suscipit orci bibendum.
Mauris semper ornare mollis. Sed vehicula id diam porta rhoncus.
Pellentesque suscipit leo nisl, non tempus erat sagittis sed.
Sed eu vestibulum urna.
Nulla facilisi.
In laoreet, metus sed tempor commodo, velit orci aliquet orci, et tempus massa enim quis dolor.
Nam ut velit eros.
`;

const sampleFromLipsum = () => {
  const sentences = lipsum.trim().replace('\n', '').split('.');
  const sentenceIndex = Math.floor(Math.random() * (sentences.length - 1));
  const sentence = sentences[sentenceIndex];
  const words = sentence.split(' ').filter(word => !!word);
  const sentenceLength = Math.ceil(Math.random() * words.length);
  return words.slice(0, sentenceLength).join(' ');
};

const generateFilterData = (): FixedListFilter => {
  const options = new Array(50).fill(null).map(() => {
    const text = sampleFromLipsum();
    return {
      label: text,
      value: text
    }
  });
  return {
    type: 'fixed_list',
    id: `example_filter`,
    title: 'Example filter',
    options
  } as const;
};

export const Default = () => {
  const wrapper = document.createElement('div');
  wrapper.classList.add('wrapper');
  const filterElement = document.createElement('ens-data-distiller-fixed-list-filter');
  const filterData = generateFilterData();
  filterElement.filterData = filterData;
  wrapper.appendChild(filterElement);

  return wrapper;
};


export default {
  title: 'Filters/Fixed list filter'
};
