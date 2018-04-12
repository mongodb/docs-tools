import {setTabPref} from './componentTabs';
import {throttle} from './util';

const headings = [];

function isVisible(elm) {
    const rect = elm.getBoundingClientRect();
    const viewHeight = Math.max(document.documentElement.clientHeight, window.innerHeight);
    return !(rect.bottom < 0 || rect.top - viewHeight >= 0);
}

function recalculate() {
    let found = false;

    for (const [headingElement, tocElement] of headings) {
        tocElement.classList.remove('active');

        if (found || !isVisible(headingElement)) {
            continue;
        }

        found = true;
        tocElement.classList.add('active');
    }
}

document.addEventListener('scroll', throttle(recalculate, 150));

function setupScrollMonitor() {
    const leftToc = document.querySelector('.left-toc');
    if (!leftToc) { return; }

    headings.length = 0;
    for (const linkElement of leftToc.querySelectorAll('a')) {
        const id = linkElement.getAttribute('href').slice(1);
        if (!id) { continue; }

        const headingElement = document.getElementById(id);
        if (!headingElement) { continue; }

        headings.push([headingElement, linkElement.parentElement]);
    }

    window.isVisible = isVisible;
    recalculate();
}

function pillClickHandler(ev) {
    const tabId = ev.target.getAttribute('data-tab-preference');
    if (!tabId) { return; }

    setTabPref({
        'tabId': tabId,
        'type': 'languages'
    }, false);
}

function setupLandingPage() {
    const guidesCategoryListElements = document.getElementsByClassName('guide-category-list');
    if (!guidesCategoryListElements.length) { return; }

    const pills = guidesCategoryListElements[0].getElementsByClassName('guide__pill');
    for (let i = 0; i < pills.length; i += 1) {
        pills[i].onclick = pillClickHandler;
    }
}

export function setup() {
    setupScrollMonitor();
    setupLandingPage();
}
