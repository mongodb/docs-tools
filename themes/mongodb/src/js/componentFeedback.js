import deluge from '../deluge/deluge';

let project = null;
let ratingPanelElement = null;

// Files on which we should not have feedback widgets
const blacklist = {
    'meta/404': true,
    'search': true
};

function getPageName() {
    const bodyElements = document.getElementsByClassName('body');
    if (!bodyElements.length) { return null; }

    const pagename = bodyElements[0].getAttribute('data-pagename');
    if (Object.prototype.hasOwnProperty.call(blacklist, pagename)) {
        return null;
    }

    return pagename;
}

export function init() {
    project = document.body.getAttribute('data-project');
    ratingPanelElement = document.getElementById('rating-panel');
}

export function setup() {
    // We require DOM storage. Don't show anything if support is not present.
    if (window.localStorage === undefined) { return; }

    if (ratingPanelElement) {
        deluge(project, getPageName(), ratingPanelElement);
    }
}
