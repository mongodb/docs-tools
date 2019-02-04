import * as componentFeedback from '../js/componentFeedback';

$(() => {
    // Monkey-patch jQuery to add the removed load() event handler.
    // This is required by the JIRA issue collector 🙄
    jQuery.fn.load = function(callback) { $(window).on('load', callback); };

    componentFeedback.init();
    componentFeedback.setup();
});
