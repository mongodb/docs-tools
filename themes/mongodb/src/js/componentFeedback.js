import {Deluge} from 'rigning';

let project = null;

// Files on which we should not have feedback widgets
const blacklist = {
    'meta/404': true,
    'search': true
};

// Set up the JIRA collector widget
let _showCollectorDialog = null;
function showCollectorDialog() {
    if (_showCollectorDialog) {
        _showCollectorDialog();
        return false;
    }

    return undefined;
}

window.ATL_JQ_PAGE_PROPS =  {
    'triggerFunction': function(showFunc) {
        _showCollectorDialog = showFunc;
    }
};

function updateLink(linkElement, pagename) {
    const escapedPagename = encodeURIComponent(pagename);

    linkElement.onclick = showCollectorDialog;
    linkElement.target = '_blank';
    linkElement.title = `Report a problem with ${pagename}.txt on Jira`;
    linkElement.href = `https://jira.mongodb.org/secure/CreateIssueDetails!init.jspa?pid=10380&issuetype=4&priority=4&summary=Comment+on%3a+%22${escapedPagename}%2Etxt%22`;
}

function updateJiraProperties(pagename) {
    window.ATL_JQ_PAGE_PROPS.fieldValues = {'summary': `Comment on: "${project}/${pagename}.txt"`};

    jQuery.ajax({
        'cache': true,
        'dataType': 'script',
        'type': 'get',
        'url': 'https://jira.mongodb.org/s/en_UScn8g8x/782/6/1.2.5/_/download/batch/com.atlassian.jira.collector.plugin.jira-issue-collector-plugin:issuecollector-embededjs/com.atlassian.jira.collector.plugin.jira-issue-collector-plugin:issuecollector-embededjs.js?collectorId=298ba4e7'
    });

    const links = document.querySelectorAll('.jirafeedback');
    for (let i = 0; i < links.length; i += 1) {
        updateLink(links[i], pagename);
    }
}

function loadPage() {
    const pagename = document.querySelector('.body').getAttribute('data-pagename');
    updateJiraProperties(pagename);
    if (Object.prototype.hasOwnProperty.call(blacklist, pagename)) {
        return;
    }

    const ratingPanelElement = document.getElementById('rating-panel');
    if (ratingPanelElement) {
        (new Deluge(project, pagename)).
            askFreeformQuestion('reason', 'What were you looking for?').
            askQuestion('findability', 'Did you find it?').
            askQuestion('accuracy', 'Was the information you found <strong>accurate</strong>?').
            askQuestion('clarity', 'Was the information <strong>clear</strong>?').
            askQuestion('fragmentation', 'Was the information you needed <strong>' +
                        'all on one page</strong>?').
            draw(ratingPanelElement);
    }
}

export function init() {
    project = document.body.getAttribute('data-project');
}

export function setup() {
    // We require DOM storage. Don't show anything if support is not present.
    if (window.localStorage === undefined) { return; }

    loadPage();
}
