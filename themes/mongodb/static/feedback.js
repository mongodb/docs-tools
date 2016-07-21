!function(){"use strict";function e(e,t){var n=[],r=!0,o=!1,i=void 0;try{for(var s,u=t.entries()[Symbol.iterator]();!(r=(s=u.next()).done);r=!0){var c=a(s.value,2),l=c[0],d=c[1];n.push(encodeURIComponent(l)+"="+encodeURIComponent(JSON.stringify(d)))}}catch(f){o=!0,i=f}finally{try{!r&&u["return"]&&u["return"]()}finally{if(o)throw i}}return e+"?"+n.join("&")}var t=function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")},n=function(){function e(e,t){for(var n=0;n<t.length;n++){var a=t[n];a.enumerable=a.enumerable||!1,a.configurable=!0,"value"in a&&(a.writable=!0),Object.defineProperty(e,a.key,a)}}return function(t,n,a){return n&&e(t.prototype,n),a&&e(t,a),t}}(),a=function(){function e(e,t){var n=[],a=!0,r=!1,o=void 0;try{for(var i,s=e[Symbol.iterator]();!(a=(i=s.next()).done)&&(n.push(i.value),!t||n.length!==t);a=!0);}catch(u){r=!0,o=u}finally{try{!a&&s["return"]&&s["return"]()}finally{if(r)throw o}}return n}return function(t,n){if(Array.isArray(t))return t;if(Symbol.iterator in Object(t))return e(t,n);throw new TypeError("Invalid attempt to destructure non-iterable instance")}}(),r="http://deluge.us-east-1.elasticbeanstalk.com/",o=function c(e){t(this,c),this.vote=e},i=function(){function e(n,a){t(this,e),this.name=n,this.caption=a,this.answer=null}return n(e,[{key:"clear",value:function(){this.answer=null}},{key:"draw",value:function(){var e=this,t=document.createElement("div"),n=document.createElement("textarea");return n.placeholder=this.caption,t.appendChild(n),t.oninput=function(){e.answer=n.value},t}}]),e}(),s=function(){function e(n,a){t(this,e),this.name=n,this.promptHtml=a,this.answer=null}return n(e,[{key:"clear",value:function(){this.answer=null}},{key:"draw",value:function(){var e=this,t=document.createElement("div");t.innerHTML=this.promptHtml;var n=document.createElement("div"),a=document.createElement("span"),r=document.createElement("span");return a.className="switch fa fa-thumbs-up good",a.onclick=function(){e.answer=!0,a.className="switch fa fa-thumbs-up good selected",r.className="switch fa fa-thumbs-down bad"},r.className="switch fa fa-thumbs-down bad",r.onclick=function(){e.answer=!1,a.className="switch fa fa-thumbs-up good",r.className="switch fa fa-thumbs-down bad selected"},n.appendChild(a),n.appendChild(r),t.appendChild(n),t}}]),e}(),u=function(){function a(e,n){t(this,a),this.project=e,this.path=n,this.questions=[],this.state="NotVoted",this.storageKey="feedback-"+e+"/"+n;var r=localStorage[this.storageKey],o=r?Date.parse(r).valueOf():-(1/0);(new Date).valueOf()<o+2592e6&&(this.state="Voted")}return n(a,[{key:"draw",value:function(e){var t=this;if("NotVoted"===this.state)return e.className="",e.innerHTML='<p>Was this page helpful?</p><a class="button" id="rate-up">Yes</a><a class="button" id="rate-down">No</a>',e.querySelector("#rate-up").onclick=function(){t.state=new o(!0),t.draw(e)},void(e.querySelector("#rate-down").onclick=function(){t.state=new o(!1),t.draw(e)});if("Voted"===this.state)return e.className="",void(e.innerHTML="<p>Thank you for your feedback!</p>");e.className="expanded";var n=this.state;e.innerText="";var a=document.createElement("ul");if(n.vote===!1){var r=document.createElement("li");r.innerText="We're sorry! Please help us improve this page.",a.appendChild(r)}var i=!0,s=!1,u=void 0;try{for(var c,l=this.questions[Symbol.iterator]();!(i=(c=l.next()).done);i=!0){var d=c.value;d.clear();var f=document.createElement("li");f.appendChild(d.draw()),a.appendChild(f)}}catch(h){s=!0,u=h}finally{try{!i&&l["return"]&&l["return"]()}finally{if(s)throw u}}var p=document.createElement("div");p.className="button-group",a.appendChild(p);var m=document.createElement("button");m.innerText="Cancel",p.appendChild(m),m.onclick=function(){t.state="NotVoted",t.draw(e)};var v=document.createElement("button");v.innerText="Submit",v.className="primary",p.appendChild(v),v.onclick=function(){var a=new Map,r=!0,o=!1,i=void 0;try{for(var s,u=t.questions[Symbol.iterator]();!(r=(s=u.next()).done);r=!0){var c=s.value;null!=c.answer&&a.set(c.name,c.answer)}}catch(l){o=!0,i=l}finally{try{!r&&u["return"]&&u["return"]()}finally{if(o)throw i}}t.sendRating(n.vote,a).then(function(){var n=(new Date).toISOString();localStorage.setItem(t.storageKey,n),t.state="Voted",t.draw(e)})["catch"](function(){console.error("Failed to send feedback"),t.state="NotVoted",t.draw(e)})},e.appendChild(a)}},{key:"askQuestion",value:function(e,t){var n=new s(e,t);return this.questions.push(n),this}},{key:"askFreeformQuestion",value:function(e,t){var n=new i(e,t);return this.questions.push(n),this}},{key:"sendRating",value:function(t,n){var a=this;return new Promise(function(o,i){n.set("v",t),n.set("p",a.project+"/"+a.path);var s=e(r,n),u=new Image;u.onload=function(){return o()},u.onerror=function(){return i()},u.src=s})}}]),a}();window.Deluge=u}();

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

        (new Deluge(project, pagename)).
            askQuestion('findability', 'Did you find what you were looking for?').
            askFreeformQuestion('reason', 'What were you looking for?').
            askQuestion('fragmentation', 'Was the information you needed all on one page?').
            askQuestion('accuracy', 'Was the information you found <strong>accurate</strong>?').
            askQuestion('clarity', 'Was the information <strong>clear</strong>?').
            askFreeformQuestion('comments', 'How can we improve this page?').
            draw(document.getElementById('rating-panel'));
    }

    window.history.onnavigate = function() { loadPage(); };
    window.addEventListener('DOMContentLoaded', loadPage);
})();
