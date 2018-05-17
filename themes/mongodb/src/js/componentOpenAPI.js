const COLLAPSED_PROPERTY = 'apiref-resource--collapsed';

// We want to let users select a path without toggling the resource's
// stage (open vs. collapsed). Only consider an event a click if the cursor
// moved less than 50 pixels in either direction before the button is lifted.
function createClickButNotSelectionHandler(element, onclick) {
    let dragStart = null;

    element.addEventListener('mousedown', (ev) => {
        if (ev.button !== 0) { return; }
        dragStart = ev;
    });

    element.addEventListener('mouseup', (ev) => {
        if (ev.button !== 0) { return; }
        const formerDragStart = dragStart;
        dragStart = null;

        if (!formerDragStart || (
            Math.abs(ev.clientX - formerDragStart.clientX) < 50 &&
            Math.abs(ev.clientY - formerDragStart.clientY) < 50)) {
            onclick();
        }
    });
}

function toggleResource(classListAction, resourceElement) {
    if (resourceElement.id) {
        const hash = `#${resourceElement.id}`;
        window.history.pushState({'href': hash}, '', hash);
    }

    resourceElement.classList[classListAction](COLLAPSED_PROPERTY);
}

function expand() {
    const hash = document.location.hash.slice(1);
    if (!hash) { return; }
    const requested = document.getElementById(hash);
    if (!requested) { return; }
    if (!requested.classList.contains('apiref-resource')) { return; }
    toggleResource('remove', requested);
}

window.addEventListener('hashchange', expand, false);

export function setup() {
    const resourceHeaderElements = document.getElementsByClassName('apiref-resource__header');
    for (let i = 0; i < resourceHeaderElements.length; i += 1) {
        const element = resourceHeaderElements[i];
        createClickButNotSelectionHandler(element,
            toggleResource.bind(null, 'toggle', element.parentElement));
    }

    expand();
}
