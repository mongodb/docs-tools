const CLASS_ACTIVATED = 'lightbox__content--activated';

const modal = document.createElement('div');
modal.className = 'lightbox__modal';
modal.title = 'click to close';
const modalContent = document.createElement('img');
modalContent.className = 'lightbox__content';
modal.appendChild(modalContent);

export function setup() {
    for (const figure of document.getElementsByClassName('lightbox')) {
        if (figure.children.length === 0 || figure.children[0].tagName !== 'IMG') {
            continue;
        }

        const img = figure.children[0];
        const wrapperElement = document.createElement('div');
        const captionElement = document.createElement('div');

        wrapperElement.className = 'lightbox__imageWrapper';
        captionElement.className = 'lightbox__caption';
        captionElement.innerText = 'click to enlarge';

        img.parentNode.replaceChild(wrapperElement, img);
        wrapperElement.appendChild(img);
        wrapperElement.appendChild(captionElement);

        wrapperElement.addEventListener('click', () => {
            document.body.appendChild(modal);
            modalContent.src = img.src;
            modalContent.alt = `${img.alt} — Enlarged`;

            modal.addEventListener('click', () => {
                modalContent.classList.remove(CLASS_ACTIVATED);
                if (!modal.parentNode) {
                    return;
                }

                modal.parentNode.removeChild(modal);
            });

            // Wait until the next DOM tick to make the fade animation work
            setTimeout(() => {
                modalContent.classList.add(CLASS_ACTIVATED);
            }, 0);
        });
    }
}
