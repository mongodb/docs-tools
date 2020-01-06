import * as componentAccordion from '../js/componentAccordion';
import * as componentAtlas from '../js/componentAtlas';
import * as componentCloseOpen from '../js/componentCloseOpen';
import * as componentCodeBlockFix from '../js/componentCodeBlockFix';
import * as componentCopyButtons from '../js/componentCopyButtons';
import * as componentEcosystemLinkTrack from '../js/componentEcosystemLinkTrack';
import * as componentFastLoad from '../js/componentFastLoad';
import * as componentFeedback from '../js/componentFeedback';
import * as componentGuides from '../js/componentGuides';
import * as componentLightbox from '../js/componentLightbox';
import * as componentOpenAPI from '../js/componentOpenAPI';
import * as componentPillStrip from '../js/componentPillStrip';
import * as componentSidebar from '../js/componentSidebar';
import * as componentStitchSidebar from '../js/componentStitchSidebar';
import * as componentTabs from '../js/componentTabs';
import * as componentThirdParty from '../js/componentThirdParty';
import * as componentToggleController from '../js/componentToggleController';
import * as componentUriWriter from '../js/componentUriwriter';
import * as componentVersionSelector from '../js/componentVersionSelector';

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

        // The anchor we wanted might have shifted around the page.
        // Reload to make sure that we're at the right place.
        if (window.location.hash) {
            window.location.hash = window.location.hash;  // eslint-disable-line no-self-assign
        }
    }
}
const fastNav = new FastNav();

$(() => {
    // Monkey-patch jQuery to add the removed load() event handler.
    // This is required by the JIRA issue collector 🙄
    jQuery.fn.load = function(callback) { $(window).on('load', callback); };

    componentThirdParty.initialize();

    fastNav.register(componentCodeBlockFix);
    fastNav.register(componentCopyButtons);
    fastNav.register(componentEcosystemLinkTrack);
    fastNav.register(componentFastLoad);
    fastNav.register(componentFeedback);
    fastNav.register(componentLightbox);
    fastNav.register(componentSidebar);
    fastNav.register(componentStitchSidebar);
    // Must precede componentTabs
    fastNav.register(componentPillStrip);
    fastNav.register(componentTabs);
    fastNav.register(componentVersionSelector);
    fastNav.register(componentThirdParty);
    fastNav.register(componentGuides);
    fastNav.register(componentOpenAPI);
    fastNav.register(componentUriWriter);
    fastNav.register(componentToggleController);
    fastNav.register(componentCloseOpen);
    fastNav.register(componentAccordion);
    if (document.referrer.indexOf('aws.amazon.com') >= 0) {
        fastNav.register(componentAtlas);
    }

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
