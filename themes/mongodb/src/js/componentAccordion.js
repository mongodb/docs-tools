const COLLAPSED_PROPERTY = 'accordion--collapsed';

function accordionShowHide(element) {
    element.classList.toggle(COLLAPSED_PROPERTY);

    const control = element.querySelector('.accordion__control');
    control.innerHTML = (control.innerHTML === 'Expand') ? 'Collapse' : 'Expand';
}

export function setup() {
    const accordionElements = document.getElementsByClassName('accordion');
    for (let i = 0; i < accordionElements.length; i += 1) {
        const element = accordionElements[i];
        const button = element.querySelector('.accordion__button');

        button.addEventListener('click', accordionShowHide.bind(this, element));
    }
}
