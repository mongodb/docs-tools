export function setup() {
    const copyableBlocks = document.getElementsByClassName('copyable-button');
    for (const copyBlock of copyableBlocks) {
        const highlightElement = copyBlock.getElementsByClassName('highlight')[0];
        if (!highlightElement) {
            return;
        }

        const copyButton = copyBlock.previousElementSibling.querySelector('a');
        if (!copyButton) {
            return;
        }

        const originalText = copyButton.innerText;
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

                copyButton.innerText = 'copied';
                window.setTimeout(() => {
                    copyButton.innerText = originalText;
                }, 1000);
            } catch (err) {
                console.error(err);
            }

            document.body.removeChild(tempElement);
        });
    }
}
