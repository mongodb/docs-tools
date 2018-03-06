/**
 * Show the appropriate tab content and hide other tab's content
 * @param {string} currentAttrValue The currently selected tab ID.
 * @returns {void}
 */
function showHideTabContent(currentAttrValue) {
    $('.tabs__content').children().
        hide();
    $(`.tabs .tabpanel-${currentAttrValue}`).show();
}

class TabsSingleton {
    constructor(key) {
        this.key = key;
        this.tabStrips = document.querySelectorAll('.tab-strip--singleton');

        // Only tab sets will have a type, init and try to retrieve
        this.type = null;
        if (this.tabStrips.length > 0) {
            this.type = this.tabStrips[0].getAttribute('data-tab-preference');
        }
    }

    /**
     * Return the tabPref object containing preferences for tab sets
     * and page specific prefs. Returns an empty object if it doesn't
     * exist.
     * @returns {object} Tab preference object.
     */
    get tabPref() {
        return JSON.parse(window.localStorage.getItem(this.key)) || {};
    }

    /**
     * Sets the tabPref object depending on whether the tab belongs
     * to set (e.g., "drivers") or if it's a one-off page.
     * @param {object} value The "tabId" and optional "type" (tab set)
     */
    set tabPref(value) {
        const tabPref = this.tabPref;

        // If "type" exists it belongs to a tab set
        if (this.type) {
            // Set top-level fields for tab set preferences
            tabPref[value.type] = value.tabId;
        } else if (tabPref.pages) {
            // Store one-off pages in the pages embedded document
            tabPref.pages[window.location.pathname] = value.tabId;
        } else {
            // Init pages embedded doc if it doesnt exist and store one-off
            tabPref.pages = {};
            tabPref.pages[window.location.pathname] = value.tabId;
        }

        // Write pref object back to localStorage
        window.localStorage.setItem(this.key, JSON.stringify(tabPref));
    }

    /**
     * Return the first singleton tab ID on the page.
     * @returns {string} The first singleton tab ID found.
     */
    getFirstTab() {
        const tabsElement = this.tabStrips[0].
            querySelector('.tab-strip__element[aria-selected=true]');
        if (!tabsElement) { return null; }

        return tabsElement.getAttribute('data-tabid');
    }

    setup() {
        if (this.tabStrips.length === 0) { return; }

        this.hideTabBars();

        for (const tabStrip of this.tabStrips) {
            for (const element of tabStrip.querySelectorAll('[data-tabid]')) {
                element.onclick = (e) => {
                    // Get the tab ID of the clicked tab
                    const tabId = e.target.getAttribute('data-tabid');
                    const type = this.tabStrips[0].getAttribute('data-tab-preference');

                    // Build the pref object to set
                    const pref = {};
                    pref.tabId = tabId;
                    pref.type = type;

                    // Check to make sure value is not null, i.e., don't do anything on "other"
                    if (tabId) {
                        // Save the users preference and re-render
                        this.tabPref = pref;
                        this.update();

                        e.preventDefault();
                    }
                };
            }
        }

        this.update();
    }

    update() {
        if (this.tabStrips.length === 0) { return; }
        let type = this.type;

        let tabPref = this.tabPref;

        if (!type && tabPref.pages && tabPref.pages[window.location.pathname]) {
            // Check if current page has a one-off page specific pref
            tabPref = tabPref.pages;
            type = window.location.pathname;
        } else if (!this.tabStrips[0].querySelector(`[data-tabid="${tabPref[type]}"]`)) {
            // If their tabPref does not exist at the top of the page use the first tab
            tabPref[type] = this.getFirstTab();
        }

        if (!tabPref) { return; }

        // Show the appropriate tab content and mark the tab as active
        showHideTabContent(tabPref[type]);
        this.showHideSelectedTab(tabPref[type]);
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
    }

    /**
     * Show only the first set of tabs at the top of the page.
     * @returns {void}
     */
    hideTabBars() {
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
}

// Create tab functionality for code examples
export function setup() {
    (new TabsSingleton('tabPref')).setup();
}
