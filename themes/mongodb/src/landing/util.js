import Velocity from 'velocity-animate';
import deluge from '../deluge/deluge';

const utils = {
    setupCopyButtons () {
        const copyableBlocks = document.getElementsByClassName('highlight');
        for (const highlightElement of copyableBlocks) {
            const text = highlightElement.innerText.trim();
            const copyButtonContainer = document.createElement('div');
            const copyButton = document.createElement('button');
            copyButtonContainer.className = 'copy-button-container';
            copyButton.className = 'copy-button';
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
    },

    setupSidebar () {
        const tocLinks = document.querySelectorAll('.toc__link');

        tocLinks.forEach((link) => {
            // handle opening & closing of the toc
            const nestedList = link.nextElementSibling;

            if (nestedList) {
                link.addEventListener('click', (e) => {
                    if (link.classList.contains('toc__link--open')) {
                        link.classList.remove('toc__link--open');
                        Velocity(nestedList, 'slideUp', {'duration': 400});
                    } else {
                        link.classList.add('toc__link--open');
                        Velocity(nestedList, 'slideDown', {'duration': 400});
                    }
                });
            }

            link.addEventListener('click', (e) => {
                tocLinks.forEach((l) => l.classList.remove('toc__link--active'));
                link.classList.add('toc__link--active');
            });
        });
    },

    // This is copied from js/componentFeedback.js
    setupFeedback () {
        // We require DOM storage. Don't show anything if support is not present.
        if (window.localStorage === undefined) { return; }

        const project = document.body.getAttribute('data-project');
        const pagename = document.querySelector('.main').getAttribute('data-pagename');
        const ratingPanelElement = document.getElementById('rating-panel');

        if (ratingPanelElement) {
            deluge(project, pagename, ratingPanelElement);
        }
    }
};

export default utils;
