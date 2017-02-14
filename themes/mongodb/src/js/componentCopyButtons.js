export function setup() {
    const copyableBlocks = document.getElementsByClassName('copyable-code');
    for (const copyBlock of copyableBlocks) {
        const highlightElement = copyBlock.getElementsByClassName('highlight')[0];
        if (!highlightElement) {
            return;
        }

        const text = highlightElement.innerText.trim();
        const copyButtonContainer = document.createElement('div');
        const copyButton = document.createElement('button');
        const copyIcon = document.createElement('span');
        copyButtonContainer.className = 'copy-button-container';
        copyIcon.className = 'fa fa-clipboard';
        copyButton.className = 'copy-button';
        copyButton.appendChild(copyIcon);
        copyButton.appendChild(document.createTextNode('Copy'));
        copyButtonContainer.appendChild(copyButton);
        highlightElement.insertBefore(copyButtonContainer, highlightElement.children[0]);
        copyButton.addEventListener('click', () => {
            const tempElement = document.createElement('textarea');
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
