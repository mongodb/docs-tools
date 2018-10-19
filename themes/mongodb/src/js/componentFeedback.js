import widgets from '../widgets/widgets';

let project = null;
let ratingPanelElement = null;

// Files on which we should not have feedback widgets
const blacklist = ['meta/404', 'search'];

function getPageName() {
    const bodyElements = document.getElementsByClassName('body');
    if (!bodyElements.length) { return null; }

    const pagename = bodyElements[0].getAttribute('data-pagename');
    if (blacklist.indexOf(pagename) >= 0) {
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

    const pageName = getPageName();
    if (ratingPanelElement) {
        widgets(project, pageName, ratingPanelElement);
    }
}
