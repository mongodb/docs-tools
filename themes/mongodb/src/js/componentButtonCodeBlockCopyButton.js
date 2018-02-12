function nodeListToArray(nodeList) {
    return Array.prototype.slice.call(nodeList);
}

export function setup() {
    const copyableBlocks = document.getElementsByClassName('bcb-copyable');
    for (const copyBlock of copyableBlocks) {
        const highlightElement = copyBlock.getElementsByClassName('highlight')[0];
        if (!highlightElement) {
            return;
        }

        const text = highlightElement.innerText.trim();
        const copyButtonContainerNodes = nodeListToArray(
            copyBlock.previousElementSibling.childNodes
        );
        const copyButton = copyButtonContainerNodes.filter(
            (child) => child.nodeName === 'A'
        )[0];

        copyButton.addEventListener('click', () => {
            const tempElement = document.createElement('textarea');
            tempElement.style.position = 'fixed';
            document.body.appendChild(tempElement);
            tempElement.value = text;
            tempElement.select();

            try {
                const successful = document.execCommand('copy');
                if (!successful) {
                    throw new Error('Failed to copy');
                }
            } catch (err) {
                console.error('Failed to copy');
                console.error(err);
            }

            document.body.removeChild(tempElement);
        });
    }
}
