const TOOLTIP_STATE_ACTIVE = 'code-button__tooltip--active';
const TOOLTIP_STATE_INACTIVE = 'code-button__tooltip--inactive';

function cancelAndWait(f, timeoutID, ms) {
    if (timeoutID >= 0) {
        window.clearTimeout(timeoutID);
    }

    return window.setTimeout(f, ms);
}

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

        const popupElement = document.createElement('div');
        popupElement.innerText = 'copied';
        popupElement.classList.add('code-button__tooltip');
        popupElement.classList.add(TOOLTIP_STATE_INACTIVE);
        let closePopupTimer = -1;

        copyButton.appendChild(popupElement);
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

                popupElement.classList.replace(TOOLTIP_STATE_INACTIVE, TOOLTIP_STATE_ACTIVE);
                closePopupTimer = cancelAndWait(() => {
                    popupElement.classList.replace(TOOLTIP_STATE_ACTIVE, TOOLTIP_STATE_INACTIVE);
                }, closePopupTimer, 1500);
            } catch (err) {
                console.error(err);
            }

            document.body.removeChild(tempElement);
        });
    }
}
