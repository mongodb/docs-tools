import {setTabPref, tabsEventDispatcher} from './componentTabs';
import {throttle} from './util';

const CLASS_EXPANDED = 'guide--expanded';
const headings = [];

function recalculate() {
    const height = document.body.clientHeight - window.innerHeight;

    // This is a bit hacky, but it mostly works. Choose our current
    // position in the page as a decimal in the range [0, 1], adding
    // our window size multiplied by 80% of the unadjusted [0, 1]
    // position.
    // The 80% is necessary because the last sections of a guide tend to
    // be shorter, and we need to make sure that scrolling to the bottom
    // highlights the last section.
    let currentPosition = document.documentElement.scrollTop / height;
    currentPosition = (document.documentElement.scrollTop +
        (currentPosition * 0.8 * window.innerHeight)) / height;

    let bestMatch = [Infinity, null];

    for (const [headingElement, tocElement] of headings) {
        tocElement.classList.remove('active');

        const headingPosition = headingElement.offsetTop / height;
        const delta = Math.abs(headingPosition - currentPosition);
        if (delta <= bestMatch[0]) {
            bestMatch = [delta, tocElement];
        }
    }

    if (bestMatch[1]) {
        bestMatch[1].classList.add('active');
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

function jumboGuideClickHandler() {
    this.classList.toggle(CLASS_EXPANDED);
}

function setupLandingPage() {
    const guidesCategoryListElement = document.getElementsByClassName('guide-category-list')[0];
    if (!guidesCategoryListElement) { return; }

    const pills = guidesCategoryListElement.getElementsByClassName('guide__pill');
    for (let i = 0; i < pills.length; i += 1) {
        pills[i].onclick = pillClickHandler;
    }

    const jumboGuideElements = document.getElementsByClassName('guide--jumbo');
    for (let i = 0; i < jumboGuideElements.length; i += 1) {
        jumboGuideElements[i].onclick = jumboGuideClickHandler;
    }
}

// Guides show the current language in the tab preferences header. Update
// that if necessary.
const showCurrentLanguageElements = document.getElementsByClassName('show-current-language');
tabsEventDispatcher.listen((ctx) => {
    if (ctx.type !== 'languages') { return; }

    for (let i = 0; i < showCurrentLanguageElements.length; i += 1) {
        showCurrentLanguageElements[i].innerText = ctx.tabId;
    }
});

export function setup() {
    setupScrollMonitor();
    setupLandingPage();
}
