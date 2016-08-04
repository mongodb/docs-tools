/* deluge v2.0 */
!function(){"use strict";function e(e,t){var n=[];return t.forEach(function(e,t){n.push(encodeURIComponent(t)+"="+encodeURIComponent(JSON.stringify(e)))}),e+"?"+n.join("&")}var t=function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")},n=function(){function e(e,t){for(var n=0;n<t.length;n++){var a=t[n];a.enumerable=a.enumerable||!1,a.configurable=!0,"value"in a&&(a.writable=!0),Object.defineProperty(e,a.key,a)}}return function(t,n,a){return n&&e(t.prototype,n),a&&e(t,a),t}}(),a="http://deluge.us-east-1.elasticbeanstalk.com/",r=function c(e){t(this,c),this.vote=e},s=function(){function e(n,a){t(this,e),this.name=n,this.caption=a,this.answer=null}return n(e,[{key:"clear",value:function(){this.answer=null}},{key:"draw",value:function(){var e=this,t=document.createElement("div"),n=document.createElement("textarea");return n.placeholder=this.caption,t.appendChild(n),t.oninput=function(){e.answer=n.value},t}}]),e}(),i=function(){function e(n,a){t(this,e),this.name=n,this.promptHtml=a,this.answer=null}return n(e,[{key:"clear",value:function(){this.answer=null}},{key:"draw",value:function(){var e=this,t=document.createElement("div");t.innerHTML=this.promptHtml;var n=document.createElement("div"),a=document.createElement("span"),r=document.createElement("span");return a.className="switch fa fa-thumbs-up good",a.onclick=function(){e.answer=!0,a.className="switch fa fa-thumbs-up good selected",r.className="switch fa fa-thumbs-down bad"},r.className="switch fa fa-thumbs-down bad",r.onclick=function(){e.answer=!1,a.className="switch fa fa-thumbs-up good",r.className="switch fa fa-thumbs-down bad selected"},n.appendChild(a),n.appendChild(r),t.appendChild(n),t}}]),e}(),o=function(){function e(n,a){t(this,e),this.name=n,this.promptHtml=a,this.answer=null}return n(e,[{key:"clear",value:function(){this.answer=null}},{key:"draw",value:function(){var t=this,n=document.createElement("div"),a=document.createElement("div");n.appendChild(a),a.innerHTML=this.promptHtml;for(var r=[],s=function(e){var a=document.createElement("span");a.onclick=function(){t.answer=e+1,console.log(t.answer),t.updateView(r)},n.appendChild(a),r.push(a)},i=0;i<e.numberOfOptions();i+=1)s(i);return this.updateView(r),n}},{key:"updateView",value:function(e){for(var t=0;t<e.length;t+=1){var n=e[t];n.className="rangestar fa",null==this.answer||t>=this.answer?n.className+=" fa-star-o":n.className+=" fa-star selected"}}}],[{key:"numberOfOptions",value:function(){return 5}}]),e}(),u=function(){function u(e,n){t(this,u),this.project=e,this.path=n,this.questions=[],this.state="NotVoted",this.storageKey="feedback-"+e+"/"+n;var a=localStorage[this.storageKey],r=a?Date.parse(a).valueOf():-(1/0);(new Date).valueOf()<r+2592e6&&(this.state="Voted")}return n(u,[{key:"draw",value:function(e){var t=this;if("NotVoted"===this.state)return e.className="",e.innerHTML='<p>Was this page helpful?</p><a class="button" id="rate-up">Yes</a><a class="button" id="rate-down">No</a>',e.querySelector("#rate-up").onclick=function(){t.state=new r(!0),t.draw(e)},void(e.querySelector("#rate-down").onclick=function(){t.state=new r(!1),t.draw(e)});if("Voted"===this.state)return e.className="",void(e.innerHTML="<p>Thank you for your feedback!</p>");e.className="expanded";var n=this.state;e.innerText="";var a=document.createElement("ul");if(n.vote===!1){var s=document.createElement("li");s.innerText="We're sorry! Please help us improve this page.",a.appendChild(s)}this.questions.forEach(function(e){e.clear();var t=document.createElement("li");t.appendChild(e.draw()),a.appendChild(t)});var i=document.createElement("div");i.className="button-group",a.appendChild(i);var o=document.createElement("button");o.innerText="Cancel",i.appendChild(o),o.onclick=function(){t.state="NotVoted",t.draw(e)};var u=document.createElement("button");u.innerText="Submit",u.className="primary",i.appendChild(u),u.onclick=function(){var a=new Map;t.questions.forEach(function(e){null!=e.answer&&a.set(e.name,e.answer)}),t.sendRating(n.vote,a).then(function(){var n=(new Date).toISOString();localStorage.setItem(t.storageKey,n),t.state="Voted",t.draw(e)})["catch"](function(){console.error("Failed to send feedback"),t.state="NotVoted",t.draw(e)})},e.appendChild(a)}},{key:"askQuestion",value:function(e,t){var n=new i(e,t);return this.questions.push(n),this}},{key:"askRangeQuestion",value:function(e,t){var n=new o(e,t);return this.questions.push(n),this}},{key:"askFreeformQuestion",value:function(e,t){var n=new s(e,t);return this.questions.push(n),this}},{key:"sendRating",value:function(t,n){var r=this;return new Promise(function(s,i){n.set("v",t),n.set("p",r.project+"/"+r.path);var o=e(a,n),u=new Image;u.onload=function(){return s()},u.onerror=function(){return i()},u.src=o})}}]),u}();window.Deluge=u}();

(function() {
    'use strict';

    // We require DOM storage. Don't show anything if support is not present.
    if (window.localStorage === undefined) { return; }

    var project = document.body.getAttribute('data-project');

    // Files on which we should not have feedback widgets
    var blacklist = {'meta/404': true, 'search': true};

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
        var escaped_pagename = encodeURIComponent(pagename);

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

        var links = document.querySelectorAll('.jirafeedback');
        for(var i = 0; i < links.length; i += 1) {
            updateLink(links[i], pagename);
        }
    }

    function loadPage() {
        var pagename = document.querySelector('.body').getAttribute('data-pagename');
        updateJiraProperties(pagename);
        if (blacklist.hasOwnProperty(pagename)) {
            return;
        }

        var ratingPanelElement = document.getElementById('rating-panel');
        if (ratingPanelElement) {
            (new Deluge(project, pagename)).
                askFreeformQuestion('reason', 'What were you looking for?').
                askQuestion('findability', 'Did you find it?').
                askQuestion('accuracy', 'Was the information you found <strong>accurate</strong>?').
                askQuestion('clarity', 'Was the information <strong>clear</strong>?').
                askQuestion('fragmentation', 'Was the information you needed <strong>all on one page</strong>?').
                draw(ratingPanelElement);
        }
    }

    window.history.onnavigate = function() { loadPage(); };
    window.addEventListener('DOMContentLoaded', loadPage);
})();
