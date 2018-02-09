const CLASS_ACTIVATED = 'lightbox__content--activated';
const CLASS_SCALABLE = 'lightbox__content--scalable';

const modal = document.createElement('div');
modal.className = 'lightbox__modal';
modal.title = 'click to close';
const modalContent = document.createElement('img');
modalContent.className = 'lightbox__content';
modal.appendChild(modalContent);

// Wrap an image in a lightbox
function wrapImage(img) {
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

        if (/\.svg$/.test(modalContent.src)) {
            modalContent.classList.add(CLASS_SCALABLE);
        } else {
            modalContent.classList.remove(CLASS_SCALABLE);
        }

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

// Intelligently wrap a figure in a lightbox if its natural area is >10%
// larger than displayed.
function wrapIfNeeded(figure, img) {
    const naturalArea = img.naturalWidth * img.naturalHeight;
    const clientArea = img.clientWidth * img.clientHeight;
    if (clientArea < (naturalArea * 0.9)) {
        wrapImage(img);
        figure.classList.add('lightbox');
    }
}

export function setup() {
    for (const figure of document.getElementsByClassName('lightbox')) {
        if (figure.children.length === 0 || figure.children[0].tagName !== 'IMG') {
            continue;
        }

        wrapImage(figure.children[0]);
    }

    // Now look at all non-explicitly-lightbox figures to see if they need
    // the same treatment.
    for (const figure of document.getElementsByClassName('figure')) {
        if (figure.children.length === 0 ||
            figure.children[0].tagName !== 'IMG' ||
            figure.classList.contains('lightbox')) {
            continue;
        }

        const img = figure.children[0];

        if (img.complete) {
            wrapIfNeeded(figure, img);
        } else {
            img.addEventListener('load', wrapIfNeeded.bind(null, figure, img));
        }
    }
}
