export const Default = () => {
  const element = document.createElement('div');
  const innerHtml = `
    <div>
      Component goes here
    </div>
  `;
  element.innerHTML = innerHtml;
  return element;
};


export default {
  title: 'Filters/Fixed list filter'
};
