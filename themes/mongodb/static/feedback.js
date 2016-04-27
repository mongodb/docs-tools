(function() {
    'use strict';

    // We require DOM storage. Don't show anything if support is not present.
    if (window.localStorage === undefined) { return; }

    const project = document.body.dataset.project;

    // Files on which we should not have feedback widgets
    const blacklist = {'meta/404': true, 'search': true};

    // Set up the JIRA collector widget
    var _showCollectorDialog;
    function showCollectorDialog() {
        if (_showCollectorDialog) {
            _showCollectorDialog();
            return false;
        }
    }
    window.ATL_JQ_PAGE_PROPS =  {
        triggerFunction: function(showFunc) {
                _showCollectorDialog = showFunc; }
    };

    function updateLink(linkElement, pagename) {
        const escaped_pagename = encodeURIComponent(pagename);

        linkElement.onclick = showCollectorDialog;
        linkElement.target = '_blank';
        linkElement.title = 'Report a problem with ' + pagename + '.txt on Jira';
        linkElement.href = 'https://jira.mongodb.org/secure/CreateIssueDetails!init.jspa?pid=10380&issuetype=4&priority=4&summary=Comment+on%3a+%22' + escaped_pagename + '%2Etxt%22';
    }

    function updateJiraProperties(pagename) {
        window.ATL_JQ_PAGE_PROPS.fieldValues = {summary: 'Comment on: "' + project + '/' + pagename + '.txt"'};

        jQuery.ajax({
            url: 'https://jira.mongodb.org/s/en_UScn8g8x/782/6/1.2.5/_/download/batch/com.atlassian.jira.collector.plugin.jira-issue-collector-plugin:issuecollector-embededjs/com.atlassian.jira.collector.plugin.jira-issue-collector-plugin:issuecollector-embededjs.js?collectorId=298ba4e7',
            type: 'get',
            cache: true,
            dataType: 'script'});

        const links = document.querySelectorAll('.jirafeedback');
        for(var i = 0; i < links.length; i += 1) {
            updateLink(links[i], pagename);
        }
    }

    function loadPage() {
        const pagename = document.querySelector('.body').dataset.pagename;
        updateJiraProperties(pagename);
        if (blacklist.hasOwnProperty(pagename)) {
            return;
        }

        // enum { no, yes, up, down }
        var voted = 'no';

        var key = 'feedback-' + window.location.pathname;
        var val = localStorage[key];
        var ratedDate = (val !== undefined)? Date.parse(val).valueOf() : -Infinity;

        // Expire the last rating after 30 days
        if ((new Date()).valueOf() < (ratedDate + (1000 * 60 * 60 * 24 * 30))) {
            voted = 'yes';
        }

        function rateFunc(rating) {
            voted = rating;
            localStorage.setItem(key, (new Date()).toJSON());
        }

        function draw() {
            var root = document.getElementById('rating-panel');
            if (root === null) { return; }

            if (voted === 'no') {
                root.innerHTML = '<p>Was this page helpful?</p> \
                                  <a class="button" id="rate-up">Yes</a> \
                                  <a class="button" id="rate-down">No</a>';
                root.querySelector('#rate-up').onclick = function() {
                    rateFunc('up');
                    draw();
                };
                root.querySelector('#rate-down').onclick = function() {
                    rateFunc('down');
                    draw();
                };
                return;
            }

            if (voted === 'up' || voted === 'yes') {
                root.innerHTML = '<p>Thank you for your feedback!</p>';
                return;
            }

            if (voted === 'down') {
                root.innerHTML = '<p>We\'re sorry! You can <a class="jira-link jirafeedback">Report a Problem</a> to help us improve this page.</p>';
                updateLink(root.querySelector('a'), pagename);
                return;
            }
        }

        draw();
    }

    window.history.onnavigate = function() { loadPage(); };
    window.addEventListener('DOMContentLoaded', loadPage);
})();
