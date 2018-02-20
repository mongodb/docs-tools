export function setup() {
    const copyableBlocks = document.getElementsByClassName('copyable-code');
    for (const copyBlock of copyableBlocks) {
        const highlightElement = copyBlock.getElementsByClassName('highlight')[0];
        if (!highlightElement) {
            return;
        }

        const text = highlightElement.innerText.trim();
        const copyButton = copyBlock.previousElementSibling.querySelector('a');
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

                copyButton.innerText = 'copied';
            } catch (err) {
                console.error(err);
            }

            document.body.removeChild(tempElement);
        });
    }
}
