const COLLAPSED_PROPERTY = 'accordion--collapsed';

/**
 * Expands and collapses the accordion. Changes the label for the
 * action, i.e., "Expand" or "Collapse"
 * @param {object} element The accordion element.
 * @returns {void}
 */
function accordionShowHide(element) {
    element.classList.toggle(COLLAPSED_PROPERTY);

    const control = element.querySelector('.accordion__action');
    control.innerHTML = (control.innerHTML === 'Expand') ? 'Collapse' : 'Expand';
}

export function setup() {
    // Get accordions and assign listeners to handle expand/collapse
    const accordionElements = document.getElementsByClassName('accordion');
    for (let i = 0; i < accordionElements.length; i += 1) {
        const element = accordionElements[i];
        const button = element.querySelector('.accordion__button');

        button.addEventListener('click', accordionShowHide.bind(this, element));
    }
}
