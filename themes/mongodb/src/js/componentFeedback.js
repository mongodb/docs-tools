import {Deluge} from 'rigning';

let project = null;

// Files on which we should not have feedback widgets
const blacklist = {
    'meta/404': true,
    'search': true
};

function loadPage() {
    const bodyElements = document.getElementsByClassName('body');
    if (!bodyElements.length) { return; }

    const pagename = bodyElements[0].getAttribute('data-pagename');
    if (Object.prototype.hasOwnProperty.call(blacklist, pagename)) {
        return;
    }

    const ratingPanelElement = document.getElementById('rating-panel');
    if (!ratingPanelElement) { return; }

    ratingPanelElement.innerText = '';
    if (ratingPanelElement) {
        (new Deluge(project, pagename, ratingPanelElement)).
            askFreeformQuestion('reason', 'What were you looking for?').
            askQuestion('findability', 'Did you find it?').
            askQuestion('accuracy', 'Was the information you found <strong>accurate</strong>?').
            askQuestion('clarity', 'Was the information <strong>clear</strong>?').
            askQuestion('fragmentation', 'Was the information you needed <strong>' +
                        'all on one page</strong>?');
    }
}

export function init() {
    project = document.body.getAttribute('data-project');
}

export function setup() {
    // We require DOM storage. Don't show anything if support is not present.
    if (window.localStorage === undefined) { return; }

    loadPage();
}
