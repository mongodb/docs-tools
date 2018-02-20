export function setup() {
    const copyableBlocks = document.getElementsByClassName('copyable-code-block');
    for (const copyBlock of copyableBlocks) {
        const highlightElement = copyBlock.getElementsByClassName('highlight')[0];
        if (!highlightElement) {
            return;
        }

        const buttonRow = copyBlock.previousElementSibling;
        const copyButton = buttonRow.getElementsByClassName('code-button--copy')[0];
        if (!copyButton) {
            return;
        }

        copyButton.addEventListener('click', () => {
            const tempElement = document.createElement('textarea');
            tempElement.style.position = 'fixed';
            document.body.appendChild(tempElement);
            tempElement.value = highlightElement.innerText.trim();
            tempElement.select();

            try {
                const successful = document.execCommand('copy');
                if (!successful) {
                    throw new Error('Failed to copy');
                }
            } catch (err) {
                console.error(err);
            }

            document.body.removeChild(tempElement);
        });
    }
}
