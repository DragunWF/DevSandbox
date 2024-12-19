const replaceAllOccurrences = (oldText, newText) => {
  // Function to replace text in a node
  function replaceTextInNode(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      // Replace all occurrences of oldText with newText
      node.nodeValue = node.nodeValue.split(oldText).join(newText);
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      // Recursively replace text in child nodes
      for (let child of node.childNodes) {
        replaceTextInNode(child);
      }
    }
  }

  // Get the body element to start the replacement
  let body = document.body;
  replaceTextInNode(body);
};

// Specific
replaceAllOccurrences("270,000.00", "150,000.00");
replaceAllOccurrences("420,000.00", "270,000.00");
