$(function() {
    'use strict';

    var docsExcludedNav = window.docsExcludedNav;

    /* Checks a whitelist for non-leaf nodes that should trigger a full page reload */
    function requiresPageload($node) {
        if (!docsExcludedNav || !docsExcludedNav.length) {
            return false;
        }

        for (var i = 0; i < docsExcludedNav.length; i++) {
            if ($node[0].href.indexOf(docsExcludedNav[i]) !== -1) {
                return true;
            }
        }
        return false;
    }

    /* currently open page */
    function isCurrentNode($node) {
        return $node.hasClass('current');
    }

    function isLeafNode($node) {
        return !$node.siblings('ul:not(.simple)').length;
    }

    function updateSidebar() {
        var $current = $('.sidebar a.current');
        if (isLeafNode($current) || requiresPageload($current) || isCurrentNode($current)) {
            $current.parent('li').addClass('selected-item');
        }
        $current.parents('ul').each(function(index, el) {
            $(el).css('display', 'block');
        });

        $('.sphinxsidebarwrapper > ul li:not(.current) > ul:not(.current)').hide();
        $('.sphinxsidebarwrapper').show();

        /*
         * This event handler defines the left-column navigation's behavior
         * The logic conforms to how sphinx generates the markup
         * The rules are:
         *  $('a.current') is the title of the content that is currently rendered (this should never be changed client-side)
         *  $('ul.current, li.current') are the set of lists that are currently expanded
         *  $('li.selected-item') is the currently highlighted item
         */
        $('.sphinxsidebarwrapper .toctree-l1').on('click', 'a', function(e) {
            var $target = $(e.currentTarget);
            if (isLeafNode($target)) {
                return; // Do a full page reload on leaf nodes
            }

            // Release notes has special behavior to click through
            if (!$target.parent().hasClass('selected-item') && requiresPageload($target)) {
                return;
            }

            e.preventDefault();

            if ($target.parent().hasClass('current')) {
                // collapse target node
                $target.parent().removeClass('current selected-item');
                $target.siblings('ul').slideUp();
            } else {

                $current.parent().removeClass('selected-item');
                // roll up all navigation up to the common ancestor
                $current.parents().add($current.siblings('ul')).each(function(index, el) {
                    var $el = $(el);
                    if ($el.has(e.currentTarget).length) {
                        return;
                    }

                    if ($el.is('ul')) {
                        $el.removeClass('current').slideUp();
                    } else {
                        $el.removeClass('current');
                    }
                });
                // add css classes for the new 'current' nav item
                $target.parent().addClass('current');
                $target.siblings('ul').slideDown(function() {
                    if (isLeafNode($target) || requiresPageload($target) || isCurrentNode($current)) {
                        $target.parent('li').addClass('selected-item');
                    }
                });
                // set new $current
                $current = $target;
            }
        });

        /* Add expand icons to indicate what's expandable and what's a link. This
           is necessary when (1) we're at a leaf node, or (2) the menu triggers
           a page load. */
        $('.sphinxsidebarwrapper > ul ul a.reference').prepend(function(index) {
            var expandElement = $('<span class="expand-icon"></span>');
            var self = $(this);

            if(!isLeafNode(self)) {
                expandElement.addClass('fa fa-plus');
            }

            return expandElement;
        });
    }

    // If the browser is sufficiently modern, make navbar links load only
    // content pieces to avoid a full page load.
    function setupFastLoad() {
        if (window.history === undefined ||
            document.querySelectorAll === undefined ||
            document.body.classList === undefined) {
            return false;
        }

        var navRootElement = document.querySelector('.sphinxsidebarwrapper');
        var bodyElement = document.querySelector('.body');
        var curLoading = {};

        // Stop loading the currently-in-progress page.
        var abortLoading = function() {
            if (curLoading.timeoutID !== undefined) {
                window.clearTimeout(curLoading.timeoutID);
            }

            if (curLoading.ajax !== undefined) {
                curLoading.ajax.abort();
            }

            curLoading = {};
        };

        // Load the specified URL.
        var loadPage = function(href, createHistory) {
            if (href === undefined) {
                console.error('Going to undefined path');
            }

            abortLoading();
            bodyElement.classList.add('loading');

            // If something goes wrong while loading, we don't want to leave
            // people without a paddle. If we can't load after a long period of
            // time, bring back the original content.
            curLoading.timeoutID = window.setTimeout(function() {
                bodyElement.classList.remove('loading');
                curLoading.timeoutID = -1;
            }, 10000);

            var startTime = new Date();
            curLoading.ajax = $.ajax({ url: href, dataType: 'html', success: function(pageText) {
                var enlapsedMs = (new Date()) - startTime;
                bodyElement.classList.remove('loading');

                var page = document.createElement('html');
                page.innerHTML = pageText;
                var title = page.querySelector('title').textContent;
                var newBody = page.querySelector('.body');
                var newNav = page.querySelector('.sphinxsidebarwrapper');

                // Fade in ONLY if we had enough time to fade out at least some.
                if (enlapsedMs > (250 / 4)) {
                    newBody.classList.add('loading');
                }

                // Change URL before loading the DOM to properly resolve URLs
                if (createHistory) {
                    window.history.pushState({ href: href }, title, href);
                }

                // Replace the DOM elements
                bodyElement.parentElement.replaceChild(newBody, bodyElement);
                bodyElement = newBody;
                navRootElement.parentElement.replaceChild(newNav, navRootElement);
                navRootElement = newNav;
                document.title = title;

                // Update the sidebar
                updateSidebar();
                setupFastLoad();

                // Prime the new DOM so that we can set up our fade-in
                // animation and scroll the new contents to the top.
                window.setTimeout(function() {
                    bodyElement.classList.remove('loading');
                    window.scroll(0, 0);
                }, 1);
            }, error: function(ev) {
                // Some browsers consider any file://-type request to be cross-origin.
                // In this case, fall back to old-style behavior.
                if (ev.status === 0 && ev.statusText === 'error') {
                    window.location = href;
                }

                console.error('Failed to load ' + href);
            }, complete: function() {
                abortLoading();
            } });
        };

        var nodes = document.querySelectorAll('.sphinxsidebarwrapper > ul a.reference');
        var handleClickFunction = function(ev) {
            // Ignore anything but vanilla click events, so that people can
            // still use special browser behaviors like open in new tab.
            if (!(ev.button !== 0 || ev.shiftKey || ev.altKey || ev.metaKey || ev.ctrlKey)) {
                ev.preventDefault();
                loadPage(ev.currentTarget.href, true);
            }
        };
        for (var i = 0; i < nodes.length; i += 1) {
            var node = nodes[i];
            if (!isLeafNode($(node)) && !requiresPageload($(node))) { continue; }

            node.addEventListener('click', handleClickFunction);
        }

        window.onpopstate = function(ev) {
            if (ev.state === null) { return; }
            loadPage(ev.state.href, false);
        };


        return true;
    }

    /* Options panel */
    $('.option-header').on('click', function(e) {
        // stop propagation to prevent the other click handler below
        // from reclosing the options panel
        e.stopPropagation();

        var $target = $(e.currentTarget);

        $target.parent().toggleClass('closed');
        $target.find('.fa-angle-down, .fa-angle-up').toggleClass('fa-angle-down fa-angle-up');
    });

    $('body').on('click', '#header-db, .sidebar, .content', function(e) {
        $('.option-popup').addClass('closed')
            .find('.fa-angle-down, .fa-angle-up').removeClass('fa-angle-down').addClass('fa-angle-up');
    });

    /* Open options panel when clicking the version */
    $('.sphinxsidebarwrapper h3 a.version').on('click', function(e) {
        e.preventDefault();

        // stop propagation to prevent reclosing of the option panel
        e.stopPropagation();
        $('.option-popup').removeClass('closed');
    });

    /* Hide toc if there aren't any items */
    if (!$('.toc > ul > li > ul > li').length) {
        $('.right-column .toc').hide();
    }

    /* Expand/collapse navbar on narrower viewports */
    $('.expand-toc-icon').on('click', function(e) {
        e.preventDefault();
        $('.sidebar').toggleClass('reveal');
    });

    /* Reset the sidebar when the viewport is wider than tablet size */
    var $window = $(window),
        $sidebar = $('.sidebar'),
        isTabletWidth = $window.width() <= 1093;
    $window.resize(function(e) {
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
    window.addEventListener("hashchange", offsetHashLink);
    if (location.hash) {
        window.setTimeout(offsetHashLink, 10);
    }
    $('.content').on('click', 'a', function(e) {
        // Fixes corner case where the user clicks the same hash link twice
        if ($(e.currentTarget).attr('href') === location.hash) {
            window.setTimeout(offsetHashLink, 10);
        }
    });

    updateSidebar();
    setupFastLoad();

    if(document.querySelector) {
        // Scroll so that the selected navbar element is in view.
        var current = document.querySelector('a.current');
        if(current) {
            current.scrollIntoView(false);
            // Scroll a bit more so that the selected element isn't hidden by
            // the Options pane button.
            var options_header = document.querySelector('.option-header');
            document.querySelector('.sidebar').scrollTop += options_header.clientHeight;
        }
    }
});
