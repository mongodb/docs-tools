import * as util from './util';

/* currently open page */
function isCurrentNode($node) {
    return $node.hasClass('current');
}

export function setup() {
    const isStitch = $('body').attr('data-project') === 'stitch';
    if (isStitch) {
        return;
    }
    let $current = $('.sidebar a.current');
    if (util.isLeafNode($current) || util.requiresPageload($current) || isCurrentNode($current)) {
        $current.parent('li').addClass('selected-item');
    }
    $current.parents('ul').each((index, el) => {
        $(el).css('display', 'block');
    });

    $('.sphinxsidebarwrapper > ul li:not(.current) > ul:not(.current)').hide();
    $('.sphinxsidebarwrapper').show();

    /*
     * This event handler defines the left-column navigation's behavior
     * The logic conforms to how sphinx generates the markup
     * The rules are:
     *  $('a.current') is the title of the content that is currently rendered
     *    (this should never be changed client-side)
     *  $('ul.current, li.current') are the set of lists that are currently expanded
     *  $('li.selected-item') is the currently highlighted item
     */
    $('.sphinxsidebarwrapper .toctree-l1').on('click', 'a', (e) => {
        const $target = $(e.currentTarget);
        if (util.isLeafNode($target)) {
            // Do a full page reload on leaf nodes
            return;
        }

        // Release notes has special behavior to click through
        if (!$target.parent().hasClass('selected-item') && util.requiresPageload($target)) {
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
            $current.parents().
                add($current.siblings('ul')).
                each((index, el) => {
                    const $el = $(el);
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
            $target.siblings('ul').slideDown(() => {
                if (util.isLeafNode($target) ||
                    util.requiresPageload($target) ||
                    isCurrentNode($current)) {
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
        const expandElement = $('<span class="expand-icon"></span>');
        const self = $(this);

        if (!util.isLeafNode(self)) {
            expandElement.addClass('docs-expand-arrow');
        }

        return expandElement;
    });
}
