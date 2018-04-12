import {tabsEventDispatcher} from './componentTabs';
import {toArray} from './util';

function pillClickHandler(tabType, ev) {
    tabsEventDispatcher.dispatch({
        'isUserAction': true,
        'tabId': ev.target.getAttribute('data-tabid'),
        'type': tabType
    });
}

let tabTypes = {};
tabsEventDispatcher.listen((ctx) => {
    for (const pillStripElement of tabTypes[ctx.type] || []) {
        const elements = pillStripElement.getElementsByClassName('guide__pill');
        for (let i = 0; i < elements.length; i += 1) {
            const element = elements[i];
            if (element.getAttribute('data-tabid') === ctx.tabId) {
                elements[i].classList.add('guide__pill--active');
            } else {
                elements[i].classList.remove('guide__pill--active');
            }
        }
    }
});

export function setup() {
    tabTypes = {};
    for (const pillStripElement of document.querySelectorAll('.pillstrip-declaration')) {
        const tabsType = pillStripElement.getAttribute('data-tab-preference');
        if (!tabsType) { continue; }

        if (tabTypes[tabsType] === undefined) { tabTypes[tabsType] = []; }
        tabTypes[tabsType].push(pillStripElement);
    }

    for (const [tabsType, pillStripElements] of Object.entries(tabTypes)) {
        const tabStrips = document.querySelectorAll(`.tabs[data-tab-preference="${tabsType}"] > .tab-strip`);
        const seenPills = {};
        const pills = [];

        for (const tabStripElement of tabStrips) {
            tabStripElement.style.display = 'none';

            let i = -1;
            let childElements = toArray(
                tabStripElement.querySelectorAll('.tab-strip__element[data-tabid]'));
            childElements = childElements.concat(
                toArray(
                    tabStripElement.querySelectorAll('.tab-strip__dropdown > li')));
            for (const childElement of childElements) {
                i += 1;
                const tabId = childElement.getAttribute('data-tabid');
                if (seenPills[tabId] !== undefined) {
                    continue;
                }

                seenPills[tabId] = true;
                pills.splice(i, 0, [tabId, childElement.innerText]);
            }
        }

        const clickHandler = pillClickHandler.bind(undefined, tabsType);
        for (const strip of pillStripElements) {
            for (const [tabId, tabTitle] of pills) {
                const pill = document.createElement('li');
                pill.className = 'guide__pill';
                pill.setAttribute('data-tabid', tabId);
                pill.innerText = tabTitle;
                pill.onclick = clickHandler;
                strip.appendChild(pill);
            }
        }
    }
}
