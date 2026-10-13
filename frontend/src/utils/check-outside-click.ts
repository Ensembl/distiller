export const checkOutsideClick = ({
  event,
  element
}: {
  event: MouseEvent;
  element: HTMLElement;
}) => {
  const scope = element.getRootNode();
  const scopeNode = event.composedPath()
    .find(node => (node as HTMLElement)
    .getRootNode?.() === scope) as HTMLElement | undefined;
  
  // A semi-magical incantation, based on how the compareDocumentPosition method works
  // (compareDocumentPosition returns an integer used as bitmask)
  const isClickInside = Boolean(
    scopeNode && (
      (scopeNode === element) ||
      (element.compareDocumentPosition(scopeNode) & Node.DOCUMENT_POSITION_CONTAINED_BY)
    )
  );

  return {
    isClickInside,
    isClickOutside: !isClickInside
  }
};