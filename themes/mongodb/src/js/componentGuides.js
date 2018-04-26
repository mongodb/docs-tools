import {setTabPref, tabsEventDispatcher} from './componentTabs';
import {throttle} from './util';

const CLASS_EXPANDED = 'guide--expanded';
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
