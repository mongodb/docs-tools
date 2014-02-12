$(function() {
    var $current = $('.sidebar a.current');
    $current.parent('li').addClass('leaf-item');
    $current.parents('ul').each(function(index, el) {
        $(el).css('display', 'block');
    });

    $('.toctree-l1').on('click', 'a', function(e) {
        var $target = $(e.currentTarget);
        if ($target.siblings('.simple').length) {
            return; // Do a full page reload on leaf nodes
        }

        e.preventDefault();

        if ($target.parent().hasClass('current')) {
            // collapse target node
            $target.removeClass('current');
            $target.siblings('ul').slideUp(function() {
                $target.parent().removeClass('current leaf-item');
            });
        } else {
            $current.removeClass('current');
            $current.parent().removeClass('leaf-item');
            // collapse current node if we're opening a new node
            if (!$current.parent().has(e.currentTarget).length) {
                $current.siblings('ul').slideUp();
            }
            // roll up everything up to the most common ancestor
            $current.parents().each(function(index, el) {
                var $el = $(el);
                if ($el.has(e.currentTarget).length) {
                    return;
                } else {
                    if ($el.is('ul')) {
                        $el.slideUp(function() {
                            $el.removeClass('current');
                        });
                    } else {
                        $el.removeClass('current');
                    }
                }
            });
            // add css classes for the new 'current' nav item
            $target.addClass('current');
            $target.siblings('ul').slideDown(function() {
                $target.parent().addClass('current leaf-item');
            });
            // set new $current
            $current = $target;
        }
    });
});