import * as componentButtonCodeBlockCopyButton from './componentButtonCodeBlockCopyButton';
import * as componentCopyButtons from './componentCopyButtons';
import * as componentFastLoad from './componentFastLoad';
import * as componentFeedback from './componentFeedback';
import * as componentLightbox from './componentLightbox';
import * as componentSidebar from './componentSidebar';
import * as componentTabs from './componentTabs';
import * as componentVersionSelector from './componentVersionSelector';

class FastNav {
    constructor() {
        this.components = [];
    }

    register(component) {
        this.components.push(component);
        if (component.init) { component.init(); }
    }

    update() {
        for (const component of this.components) {
            component.setup(this);
        }
    }
}
const fastNav = new FastNav();

$(() => {
    fastNav.register(componentCopyButtons);
    fastNav.register(componentButtonCodeBlockCopyButton);
    fastNav.register(componentFastLoad);
    fastNav.register(componentFeedback);
    fastNav.register(componentLightbox);
    fastNav.register(componentSidebar);
    fastNav.register(componentTabs);
    fastNav.register(componentVersionSelector);

    /* Hide toc if there aren't any items */
    if (!$('.toc > ul > li > ul > li').length) {
        $('.right-column .toc').hide();
    }

    /* Expand/collapse navbar on narrower viewports */
    $('.expand-toc-icon').on('click', (e) => {
        e.preventDefault();
        $('.sidebar').toggleClass('reveal');
    });

    /* Reset the sidebar when the viewport is wider than tablet size */
    const $window = $(window);
    const $sidebar = $('.sidebar');
    let isTabletWidth = $window.width() <= 1093;
    $window.resize((e) => {
        if (isTabletWidth && $window.width() > 1093) {
            isTabletWidth = false;
            $sidebar.removeClass('reveal');
        } else if (!isTabletWidth && $window.width() <= 1093) {
            isTabletWidth = true;
        }
    });

    /* Adjust the scroll location to account for our fixed header */
    function offsetHashLink() {
        if (location.hash && document.getElementById(location.hash.substr(1))) {
            $(window).scrollTop(window.scrollY - 75);
        }
    }
    window.addEventListener('hashchange', offsetHashLink);
    if (location.hash) {
        window.setTimeout(offsetHashLink, 10);
    }
    $('.content').on('click', 'a', (e) => {
        // Fixes corner case where the user clicks the same hash link twice
        if ($(e.currentTarget).attr('href') === location.hash) {
            window.setTimeout(offsetHashLink, 10);
        }
    });

    // Update dynamic page features
    fastNav.update();

    if (document.querySelector) {
        // Scroll so that the selected navbar element is in view.
        const current = document.querySelector('a.current');
        if (current) {
            current.scrollIntoView(false);
        }
    }
});
