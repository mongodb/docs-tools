import {getTabPref, tabsEventDispatcher} from './componentTabs';

const STYLE_SELECTED = 'guide__deploymentpill--active';
const STYLE = 'guide__pill';
const STYLE_DEPLOY = 'guide__deploymentpill';
const STYLE_DEPLOYTEXT = 'show-current-deployment';


function setToggleState(id) {
    const elements = document.getElementsByClassName(STYLE);
    for (let i = 0; i < elements.length; i += 1) {
        const element = elements[i];
        if (element.getAttribute('data-tabid') === id) {
            elements[i].classList.add(STYLE_SELECTED);
        } else {
            elements[i].classList.remove(STYLE_SELECTED);
        }
    }
    if (document.getElementsByClassName(STYLE_DEPLOYTEXT).length > 0) {
        document.getElementsByClassName(STYLE_DEPLOYTEXT)[0].innerHTML = id;
    }
}

tabsEventDispatcher.listen((ctx) => {
    if (ctx.type === 'cloud') {
        setToggleState(ctx.tabId);
    }
});

function dispatchState(cloudState) {
    tabsEventDispatcher.dispatch({
        'isUserAction': true,
        'tabId': cloudState,
        'type': 'cloud'
    });
}

function addListenersToPills(element) {
    element.addEventListener('click', (event) => {
        tabsEventDispatcher.dispatch({
            'isUserAction': true,
            'tabId': event.target.innerHTML,
            'type': 'cloud'
        });
    });
}

function getTabNode(nodeName, pref) {
    const element = document.createElement('li');
    element.classList.add(STYLE);
    element.classList.add(STYLE_DEPLOY);
    element.setAttribute('data-tabid', nodeName);
    element.innerHTML = nodeName;
    addListenersToPills(element);
    setToggleState(nodeName);
    return element;
}

export function setup() {
    // we use a sort of reflection to figure out if this needs to display

    const parent = document.getElementsByClassName('guide-prefs__deploy')[0];
    if (parent === undefined) {
        return;
    }
    if (document.getElementsByClassName('tabpanel-cloud').length === 0 &&
        document.getElementsByClassName('guide-prefs__deploy').length > 0) {
        document.getElementsByClassName('guide-prefs__deploy')[0].style.display = 'none';
        return;
    }
    const tabPrefs = getTabPref();
    if (tabPrefs.cloud === undefined) {
        tabPrefs.cloud = 'local';
    }
    // setToggleState(tabPrefs.cloud);
    const list = document.createElement('ul');
    list.classList.add('guide__pills');
    list.classList.add('pillstrip-declaration');
    list.setAttribute('role', 'tablist');
    list.setAttribute('data-tab-preference', 'cloud');
    list.appendChild(getTabNode('cloud', tabPrefs.cloud));
    list.appendChild(getTabNode('local', tabPrefs.cloud));
    parent.appendChild(list);
    setToggleState(tabPrefs.cloud);
    dispatchState(tabPrefs.cloud);
}
