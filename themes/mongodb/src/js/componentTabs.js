import {Dispatcher, toArray} from './util';

export const tabsEventDispatcher = new Dispatcher();

/**
 * Show only the first set of tabs at the top of the page.
 * @returns {void}
 */
function hideTabBars() {
    const isTop = document.querySelector('.tabs-top');
    if (isTop) {
        const tabBars = $('.tab-strip--singleton');
        const mainTabBar = tabBars.first();
        // Remove any additional tab bars
        tabBars.slice(1).
            detach();
        // Position the main tab bar after the page title
        mainTabBar.
            detach().
            insertAfter('h1').
            first();
    }
}

/**
 * Return the tabPref object containing preferences for tab sets
 * and page specific prefs. Returns an empty object if it doesn't
 * exist.
 * @returns {object} Tab preference object.
 */
function getTabPref() {
    return JSON.parse(window.localStorage.getItem('tabPref')) || {};
}

/**
 * Sets the tabPref object depending on whether the tab belongs
 * to set (e.g., "drivers") or if it's a one-off page.

 * @param {object} pref The "tabId" and "type" (tab set)
 * @param {boolean} anonymous Whether or not the tab being configured is anonymous.
 * @returns {void}
 */
function setTabPref(pref, anonymous) {
    const tabPref = getTabPref();

    if (anonymous) {
        if (!tabPref.pages) {
            tabPref.pages = {};
        }

        tabPref.pages[window.location.pathname] = pref.tabId;
    } else {
        // Set top-level fields for tab set preferences
        tabPref[pref.type] = pref.tabId;
    }

    // Write pref object back to localStorage
    window.localStorage.setItem('tabPref', JSON.stringify(tabPref));
}

let tabSets = {};
class TabSet {
    constructor(tabType, anonymous, tabStripElements, tabContents) {
        this.type = tabType;
        this.tabStrips = tabStripElements;
        this.tabContents = tabContents;
        this.anonymous = anonymous;

        // A set of all tabIds contained within this TabSet.
        this.tabIds = {};
    }

    /**
     * Return the first singleton tab ID on the page.
     * @returns {string} The first singleton tab ID found.
     */
    getFirstTabId() {
        const tabsElement = this.tabStrips[0].
            querySelector('.tab-strip__element[aria-selected=true]');
        if (!tabsElement) { return null; }

        return tabsElement.getAttribute('data-tabid');
    }

    setup() {
        if (this.tabStrips.length === 0) { return; }

        hideTabBars();

        for (const tabStrip of this.tabStrips) {
            for (const element of tabStrip.querySelectorAll('[data-tabid]')) {
                this.tabIds[element.getAttribute('data-tabid')] = true;

                element.onclick = (e) => {
                    // Get the initial position of the tab clicked
                    // to avoid page jumping after new tab is selected
                    const initRect = element.getBoundingClientRect();

                    // Get the position where the user scrolled to
                    const initScrollY = window.scrollY;

                    // Calc the distance from the tab strip to the top
                    // of whatever the user has scrolled to
                    const offset = initScrollY - initRect.y;

                    // Get the tab ID of the clicked tab
                    const tabId = e.target.getAttribute('data-tabid');

                    // Build the pref object to set
                    const pref = {};
                    pref.tabId = tabId;
                    pref.type = this.type;

                    // Check to make sure value is not null, i.e., don't do anything on "other"
                    if (tabId) {
                        // Save the users preference and re-render
                        this.update(tabId, true);

                        // Get the position of tab strip after re-render
                        const rects = element.getBoundingClientRect();

                        // Reset the scroll position of the browser
                        window.scrollTo(rects.x, rects.y + offset);

                        e.preventDefault();
                    }
                };
            }
        }

        this.update(null, false);
    }

    update(tabId, isUserAction) {
        if (this.tabStrips.length === 0) { return; }

        if (!tabId) {
            const tabPref = getTabPref();
            if (this.anonymous && tabPref.pages && tabPref.pages[window.location.pathname]) {
                // Check if current page has a one-off page specific pref
                tabId = tabPref.pages[window.location.pathname];
            } else if (tabPref[this.type]) {
                tabId = tabPref[this.type];
            }
        }

        if (!tabId || !this.tabIds[tabId]) {
            tabId = this.getFirstTabId();

            if (!tabId) { return; }
        }

        // Show the appropriate tab content and mark the tab as active
        tabsEventDispatcher.dispatch({
            'isUserAction': isUserAction,
            'tabId': tabId,
            'type': this.type
        });
    }

    /**
     * Marks the selected tab as active, handles special cases for the dropdown
     * @param {string} currentAttrValue The currently selected tab ID.
     * @returns {void}
     */
    showHideSelectedTab(currentAttrValue) {
        for (const tabStrip of this.tabStrips) {
            // Get the <a>, <li> and <ul> of the selected tab
            const tabLink = $(tabStrip.querySelector(`[data-tabid="${currentAttrValue}"]`));
            if (!tabLink.length) {
                continue;
            }

            const tabList = tabLink.parent('ul');

            // Get the dropdown <a> and <li> for active and label management
            const dropdownLink = $(tabStrip.querySelector('.dropdown-toggle'));
            const dropdownListItem = $(tabStrip.querySelector('.dropdown'));

            // Set the active tab, if it's on the dropdown set it to active and change label
            if (tabList.hasClass('dropdown-menu')) {
                // Use first so text doesn't repeat if more than one set of tabs
                dropdownLink.text(`${tabLink.first().text()}`).append('<span class="caret"></span>');
                dropdownListItem.
                    attr('aria-selected', true).
                    siblings().
                    attr('aria-selected', false);
            } else {
                // Set a non-dropdown tab to active, and change the dropdown label back to "Other"
                tabLink.
                    attr('aria-selected', true).
                    siblings().
                    attr('aria-selected', false);
                dropdownLink.text('Other ').append('<span class="caret"></span>');
            }
        }

        const className = `tabpanel-${currentAttrValue}`;
        for (const contentElement of this.tabContents) {
            for (const childElement of contentElement.children) {
                if (childElement.classList.contains(className)) {
                    childElement.style.display = 'block';
                } else {
                    childElement.style.display = 'none';
                }
            }
        }
    }

    static register(tabElement) {
        const tabStripElements = toArray(tabElement.getElementsByClassName('tab-strip--singleton'));
        if (!tabStripElements.length) { return; }

        const tabContent = tabElement.querySelector('.tabs__content');
        let tabType = tabElement.getAttribute('data-tab-preference');
        let anonymous = false;

        // If there is no specified tab type, use the first tab's ID
        if (!tabType) {
            const tabs = tabStripElements[0].getElementsByClassName('tab-strip__element');
            if (!tabs.length) {
                return;
            }

            tabType = tabs[0].getAttribute('data-tabid');

            if (!tabType) {
                return;
            }

            tabType = `anonymous-${tabType}`;
            anonymous = true;
        }

        if (tabSets[tabType]) {
            const tabSet = tabSets[tabType];
            tabSet.tabStrips = tabSet.tabStrips.concat(tabStripElements);
            tabSet.tabContents.push(tabContent);
            return;
        }

        const tabSet = new TabSet(tabType, anonymous, tabStripElements, [tabContent], false);
        tabSets[tabType] = tabSet;
    }
}

// Listen for state changes necessitating a redraw
tabsEventDispatcher.listen((ctx) => {
    const tabSet = tabSets[ctx.type];
    if (tabSet) {
        // Only save our new preference if we are responding to user input.
        if (ctx.isUserAction) {
            setTabPref(ctx, tabSet.anonymous);
        }

        tabSet.showHideSelectedTab(ctx.tabId);
    }
});

// Create tab functionality for code examples
export function setup() {
    tabSets = {};

    const tabsElements = document.getElementsByClassName('tabs');
    for (let i = 0; i < tabsElements.length; i += 1) {
        TabSet.register(tabsElements[i]);
    }

    for (const tabSet of Object.values(tabSets)) {
        tabSet.setup();
    }
}
