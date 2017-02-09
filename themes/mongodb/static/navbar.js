$(function() {
    'use strict';

    function fullDocsPath(base) {
        var body = document.getElementsByClassName('body')[0];
        var path = body.getAttribute('data-pagename');

        // skip if pagename is undefined (index.html)
        if (path == 'index') {
            path = '';
        } else if (path) {
          path = path + '/';
        }

        return '/' + base + '/' + path;
    }

    /* Wrapper around XMLHttpRequest to make it more convenient
     * Calls options.success(response, url), providing the response text and
     *         the canonical URL after redirects.
     * Calls options.error() on error.
     * jQuery's wrapper does not supply XMLHttpRequest.responseURL, making
     * this rewrite necessary. */
    function xhrGet(url, options) {
        var xhr = new XMLHttpRequest();

        xhr.onload = function() {
            if(xhr.status >= 200 && xhr.status < 400) {
                options.success(xhr.responseText, xhr.responseURL);
                options.complete();
            } else {
                options.error();
                options.complete();
            }
        };

        xhr.onerror = function() {
            options.error();
            options.complete();
        };

        xhr.open('GET', url, true);
        try {
            xhr.send();
        } catch(err) {
            options.error();
            options.complete();
        }
    }

    /* Checks a whitelist for non-leaf nodes that should trigger a full page reload */
    function requiresPageload($node) {
        var docsExcludedNav = window.docsExcludedNav;

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

    function updateVersionSelector() {
        $('.version-selector').on('click', function(e) {
            e.preventDefault();
            var base = $(e.currentTarget).data('path');
            window.location.href = fullDocsPath(base);
        });
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

    function createCopyButtons() {
        var copyableBlocks = document.getElementsByClassName('copyable-code');
        for(var i = 0; i < copyableBlocks.length; i += 1) {
            // IIFE to support loop scope without needing let
            ;(function() {
                var copyBlock = copyableBlocks[i];
                var highlightElement = copyBlock.getElementsByClassName('highlight')[0];
                if(!highlightElement) {
                    return;
                }

                var text = highlightElement.innerText.trim();
                var copyButtonContainer = document.createElement('div');
                var copyButton = document.createElement('button');
                var copyIcon = document.createElement('span');
                copyButtonContainer.className = 'copy-button-container';
                copyIcon.className = 'fa fa-clipboard';
                copyButton.className = 'copy-button';
                copyButton.appendChild(copyIcon);
                copyButton.appendChild(document.createTextNode('Copy'));
                copyButtonContainer.appendChild(copyButton);
                highlightElement.insertBefore(copyButtonContainer, highlightElement.children[0]);
                copyButton.addEventListener('click', function() {
                    var tempElement = document.createElement('textarea');
                    document.body.appendChild(tempElement);
                    tempElement.value = text;
                    tempElement.select();

                    try {
                        var successful = document.execCommand('copy');
                        if (!successful) {
                            throw new Error('Failed to copy');
                        }
                    } catch (err) {
                        console.error('Failed to copy');
                        console.error(err);
                    }

                    document.body.removeChild(tempElement);
                })
            })();
        }
    }


    // Create tab functionality for code examples
    function setupTabs() {
        var currentAttrValue
        // Check if the user has a preference stored, if so load it
        if (localStorage.getItem("languagePref")) {
            currentAttrValue = localStorage.getItem("languagePref");
        } else {
            currentAttrValue = document.querySelector('.nav-tabs > .active > [href]').getAttribute('href')
        }

        // Show the appropriate tab content and mark the tab as active
        showHideTabContent(currentAttrValue);
        showHideSelectedTab(currentAttrValue);

        document.querySelectorAll('.tabs .nav-tabs a').forEach(function(element) {
            element.onclick = function(e) {
                // Get the href of the clicked tab
                var currentAttrValue = element.getAttribute('href');

                // Check to make sure value is not null, i.e., don't do anything on "other"
                if (currentAttrValue) {
                    // Save the users preference
                    localStorage.setItem("languagePref", currentAttrValue);

                    // Show the appropriate tab content and mark the tab as active
                    showHideTabContent(currentAttrValue);
                    showHideSelectedTab(currentAttrValue);

                    e.preventDefault();
                }
            };
        });
    }

    // Show the appropriate tab content and hide other tab's content
    function showHideTabContent(currentAttrValue) {
        $('.tabs ' + currentAttrValue).show().siblings().hide();
    }

    // Marks the selected tab as active, handles special cases for the dropdown
    function showHideSelectedTab(currentAttrValue) {
        // Get the <a>, <li> and <ul> of the selected tab
        var tabLink = $('a[href='+ currentAttrValue +']');
        var tabListItem = tabLink.parent('li');
        var tabList = tabListItem.parent('ul');

         // Get the dropdown <a> and <li> for active and label management
         var dropdownLink = $('.tabs .dropdown-toggle');
         var dropdownListItem = $('.tabs .dropdown');

        // Set the active tab, if it's on the dropdown set it to active and change label
        if (tabList.hasClass('dropdown-menu')) {
            dropdownLink.text(tabLink.text() + ' ').append('<span class="caret"></span>');
            dropdownListItem.addClass('active').siblings().removeClass('active');
        } else {
            // Set a non-dropdown tab to active, and change the dropdown label back to "Other"
            tabListItem.addClass('active').siblings().removeClass('active');
            dropdownLink.text('Other ').append('<span class="caret"></span>');
        }
    }

    // If the browser is sufficiently modern, make navbar links load only
    // content pieces to avoid a full page load.
    function setupFastLoad() {
        if (window.history === undefined ||
            document.querySelectorAll === undefined ||
            document.body.classList === undefined ||
            (new XMLHttpRequest()).responseURL === undefined) {
            return false;
        }

        var navRootElement = document.querySelector('.sphinxsidebarwrapper');
        var bodyElement = document.querySelector('.body');
        var curLoading = {};

        // Set up initial state so we can return to our initial landing page.
        window.history.replaceState({ href: window.location.href },
                                    document.querySelector('title').textContent,
                                    window.location.href);

        // Stop loading the currently-in-progress page.
        var abortLoading = function() {
            if (curLoading.timeoutID !== undefined) {
                window.clearTimeout(curLoading.timeoutID);
            }

            if (curLoading.xhr !== undefined) {
                curLoading.xhr.abort();
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
            curLoading.xhr = xhrGet(href, { success: function(pageText, trueUrl) {
                var enlapsedMs = (new Date()) - startTime;
                bodyElement.classList.remove('loading');

                // Change URL before loading the DOM to properly resolve URLs
                if (createHistory) {
                    window.history.pushState({ href: trueUrl }, '', trueUrl);
                }

                var page = document.createElement('html');
                page.innerHTML = pageText;
                var title = page.querySelector('title').textContent;
                var newBody = page.querySelector('.body');
                var newNav = page.querySelector('.sphinxsidebarwrapper');

                // Fade in ONLY if we had enough time to start fading out.
                if (enlapsedMs > (250 / 4)) {
                    newBody.classList.add('loading');
                }

                // Replace the DOM elements
                bodyElement.parentElement.replaceChild(newBody, bodyElement);
                bodyElement = newBody;
                navRootElement.parentElement.replaceChild(newNav, navRootElement);
                navRootElement = newNav;
                document.title = title;

                // Update dynamic page features
                updateSidebar();
                setupFastLoad();
                updateVersionSelector();
                createCopyButtons();
                setupTabs();

                if (window.history.onnavigate) {
                    window.history.onnavigate();
                }

                // Prime the new DOM so that we can set up our fade-in
                // animation and scroll the new contents to the top.
                window.setTimeout(function() {
                    bodyElement.classList.remove('loading');

                    // Scroll to the top of the page only if this is a new history entry.
                    if(createHistory) {
                        window.scroll(0, 0);
                    }
                }, 1);
            }, error: function(err) {
                // Some browsers consider any file://-type request to be cross-origin.
                // Upon any kind of error, fall back to classic behavior
                console.error('Failed to load ' + href);
                window.location = href;
            }, complete: function() {
                abortLoading();
            } });
        };

        // Set up fastnav links
        var nodes = document.querySelectorAll('.sphinxsidebarwrapper > ul a.reference.internal');
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
    window.addEventListener('hashchange', offsetHashLink);
    if (location.hash) {
        window.setTimeout(offsetHashLink, 10);
    }
    $('.content').on('click', 'a', function(e) {
        // Fixes corner case where the user clicks the same hash link twice
        if ($(e.currentTarget).attr('href') === location.hash) {
            window.setTimeout(offsetHashLink, 10);
        }
    });

    // Update dynamic page features
    updateSidebar();
    setupFastLoad();
    updateVersionSelector();
    createCopyButtons();
    setupTabs();

    if(document.querySelector) {
        // Scroll so that the selected navbar element is in view.
        var current = document.querySelector('a.current');
        if(current) {
            current.scrollIntoView(false);
        }
    }
});
