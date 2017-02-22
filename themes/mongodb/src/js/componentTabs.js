// Show the appropriate tab content and hide other tab's content
function showHideTabContent(currentAttrValue) {
    // Remove the # to find <div> w/ class of the currentAttrValue
    if (currentAttrValue.charAt(0) === '#') {
        currentAttrValue = currentAttrValue.substring(1);
    }
    $(`.tabs .${currentAttrValue}`).
        show().
        siblings().
        hide();
}

// Marks the selected tab as active, handles special cases for the dropdown
function showHideSelectedTab(currentAttrValue) {
    // Get the <a>, <li> and <ul> of the selected tab
    const tabLink = $(`a[href=${currentAttrValue}]`);
    const tabListItem = tabLink.parent('li');
    const tabList = tabListItem.parent('ul');

     // Get the dropdown <a> and <li> for active and label management
    const dropdownLink = $('.nav.nav-tabs.nav-justified .dropdown-toggle');
    const dropdownListItem = $('.nav.nav-tabs.nav-justified .dropdown');

    // Set the active tab, if it's on the dropdown set it to active and change label
    if (tabList.hasClass('dropdown-menu')) {
        // Use first so text doesn't repeat if more than one set of tabs
        dropdownLink.text(`${tabLink.first().text()}`).append('<span class="caret"></span>');
        dropdownListItem.
            addClass('active').
            siblings().
            removeClass('active');
    } else {
        // Set a non-dropdown tab to active, and change the dropdown label back to "Other"
        tabListItem.
            addClass('active').
            siblings().
            removeClass('active');
        dropdownLink.text('Other ').append('<span class="caret"></span>');
    }
}

// Show only the first set of tabs at the top of the page
function hideTabBars() {
    const tabBars = $('.nav.nav-tabs.nav-justified');
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

// Create tab functionality for code examples
export function setup() {
    let initialAttrValue = null;

    // Check if the user has a preference stored, if so load it
    if (localStorage.getItem('languagePref')) {
        initialAttrValue = localStorage.getItem('languagePref');
    } else {
        const tabsElement = document.querySelector('.nav-tabs > .active > [href]');
        if (!tabsElement) {
            return;
        }

        initialAttrValue = tabsElement.getAttribute('href');
    }

    // Show the appropriate tab content and mark the tab as active
    showHideTabContent(initialAttrValue);
    showHideSelectedTab(initialAttrValue);
    hideTabBars();

    document.querySelectorAll('.nav.nav-tabs.nav-justified a').forEach((element) => {
        element.onclick = function(e) {
            // Get the href of the clicked tab
            const currentAttrValue = element.getAttribute('href');

            // Check to make sure value is not null, i.e., don't do anything on "other"
            if (currentAttrValue) {
                // Save the users preference
                localStorage.setItem('languagePref', currentAttrValue);

                // Show the appropriate tab content and mark the tab as active
                showHideTabContent(currentAttrValue);
                showHideSelectedTab(currentAttrValue);
                hideTabBars();

                e.preventDefault();
            }
        };
    });
}
