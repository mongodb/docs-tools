!function(){"use strict";function t(){for(var t=0,e=document.getElementsByClassName("copyable-code");t<e.length;t+=1){var n=function(){var n=e[t].getElementsByClassName("highlight")[0];if(!n)return{};var o=n.innerText.trim(),a=document.createElement("div"),r=document.createElement("button"),i=document.createElement("span");a.className="copy-button-container",i.className="fa fa-clipboard",r.className="copy-button",r.appendChild(i),r.appendChild(document.createTextNode("Copy")),a.appendChild(r),n.insertBefore(a,n.children[0]),r.addEventListener("click",function(){var t=document.createElement("textarea");document.body.appendChild(t),t.value=o,t.select();try{if(!document.execCommand("copy"))throw new Error("Failed to copy")}catch(t){console.error("Failed to copy"),console.error(t)}document.body.removeChild(t)})}();if(n)return n.v}}function e(t){return!t.siblings("ul:not(.simple)").length}function n(t){var e=window.docsExcludedNav;if(!e||!e.length)return!1;for(var n=0;n<e.length;n+=1)if(-1!==t[0].href.indexOf(e[n]))return!0;return!1}function o(t,e){var n=new XMLHttpRequest;n.onload=function(){n.status>=200&&n.status<400?(e.success(n.responseText,n.responseURL),e.complete()):(e.error(),e.complete())},n.onerror=function(){e.error(),e.complete()},n.open("GET",t,!0);try{n.send()}catch(t){e.error(),e.complete()}}function a(t){function a(){void 0!==c.timeoutID&&window.clearTimeout(c.timeoutID),void 0!==c.xhr&&c.xhr.abort(),c={}}function r(e,n){void 0===e&&console.error("Going to undefined path"),a(),u.classList.add("loading"),c.timeoutID=window.setTimeout(function(){u.classList.remove("loading"),c.timeoutID=-1},1e4);var r=new Date;c.xhr=o(e,{complete:function(){a()},error:function(t){console.error("Failed to load "+e),window.location=e},success:function(e,o){var a=new Date-r;u.classList.remove("loading"),n&&window.history.pushState({href:o},"",o);var i=document.createElement("html");i.innerHTML=e;var c=i.querySelector("title").textContent,l=i.querySelector(".body"),d=i.querySelector(".sphinxsidebarwrapper");a>62.5&&l.classList.add("loading"),u.parentElement.replaceChild(l,u),u=l,s.parentElement.replaceChild(d,s),s=d,document.title=c,t.update(),window.history.onnavigate&&window.history.onnavigate(),window.setTimeout(function(){u.classList.remove("loading"),n&&window.scroll(0,0)},1)}})}function i(t){0!==t.button||t.shiftKey||t.altKey||t.metaKey||t.ctrlKey||(t.preventDefault(),r(t.currentTarget.href,!0))}if(void 0===window.history||void 0===document.querySelectorAll||void 0===document.body.classList||void 0===(new XMLHttpRequest).responseURL)return!1;var s=document.querySelector(".sphinxsidebarwrapper"),u=document.querySelector(".body"),c={};window.history.replaceState({href:window.location.href},document.querySelector("title").textContent,window.location.href);for(var l=document.querySelectorAll(".sphinxsidebarwrapper > ul a.reference.internal"),d=0;d<l.length;d+=1){var f=l[d];(e($(f))||n($(f)))&&f.addEventListener("click",i)}return window.onpopstate=function(t){null!==t.state&&r(t.state.href,!1)},!0}function r(){}function i(t){for(var e,n,o=arguments,a=1,r=arguments.length;a<r;a++){n=o[a];for(e in n)t[e]=n[e]}return t}function s(t,e){e.appendChild(t)}function u(t,e,n){e.insertBefore(t,n)}function c(t){t.parentNode.removeChild(t)}function l(t,e){for(;t.nextSibling&&t.nextSibling!==e;)t.parentNode.removeChild(t.nextSibling)}function d(t,e,n){for(var o=n;o<t.length;o+=1)t[o]&&t[o].destroy(e)}function f(t){return document.createElement(t)}function h(t){return document.createTextNode(t)}function p(){return document.createComment("")}function m(t,e,n){t.addEventListener(e,n,!1)}function g(t,e,n){t.removeEventListener(e,n,!1)}function v(t,e,n){t.setAttribute(e,n)}function y(t,e){return t!==e||t&&"object"==typeof t||"function"==typeof t}function _(t,e,n,o){for(var a in e)if(a in n){var r=n[a],i=o[a];if(y(r,i)){var s=e[a];if(!s)continue;for(var u=0;u<s.length;u+=1){var c=s[u];c.__calling||(c.__calling=!0,c.call(t,r,i),c.__calling=!1)}}}}function b(t){return t?this._state[t]:this._state}function w(t,e){var n=this,o=t in this._handlers&&this._handlers[t].slice();if(o)for(var a=0;a<o.length;a+=1)o[a].call(n,e)}function C(t,e,n){var o=n&&n.defer?this._observers.post:this._observers.pre;return(o[t]||(o[t]=[])).push(e),n&&!1===n.init||(e.__calling=!0,e.call(this,this._state[t]),e.__calling=!1),{cancel:function(){var n=o[t].indexOf(e);~n&&o[t].splice(n,1)}}}function x(t,e){if("teardown"===t)return this.on("destroy",e);var n=this._handlers[t]||(this._handlers[t]=[]);return n.push(e),{cancel:function(){var t=n.indexOf(e);~t&&n.splice(t,1)}}}function k(t){this._set(i({},t)),this._root._flush()}function j(){var t=this;if(this._renderHooks)for(;this._renderHooks.length;)t._renderHooks.pop()()}function S(t,e,n,o){(o||"answer"in e&&y(t.answer,n.answer))&&(t.upvoteSelected=e.upvoteSelected=st.computed.upvoteSelected(t.answer),t.downvoteSelected=e.downvoteSelected=st.computed.downvoteSelected(t.answer))}function q(t,e){function n(t){e.change(!0)}function o(t){e.change(!1)}var a,r,i=f("div"),d=f("noscript");s(d,i);var p=f("noscript");s(p,i);var v=t.caption;d.insertAdjacentHTML("afterend",v);var y=h("\n"),_=f("div"),b=f("span");s(b,_),b.className=a="switch fa fa-thumbs-up good "+t.upvoteSelected,m(b,"click",n),s(h("\n    "),_);var w=f("span");return s(w,_),w.className=r="switch fa fa-thumbs-down bad "+t.downvoteSelected,m(w,"click",o),{mount:function(t,e){u(i,t,e),u(y,t,e),u(_,t,e)},update:function(t,e){v!==(v=e.caption)&&(l(d,p),d.insertAdjacentHTML("afterend",v)),a!==(a="switch fa fa-thumbs-up good "+e.upvoteSelected)&&(b.className=a),r!==(r="switch fa fa-thumbs-down bad "+e.downvoteSelected)&&(w.className=r)},unmount:function(){l(d,p),c(i),c(y),c(_)},destroy:function(){g(b,"click",n),g(w,"click",o)}}}function N(t){t=t||{},this._state=i(st.data(),t.data),S(this._state,this._state,{},!0),this._observers={pre:Object.create(null),post:Object.create(null)},this._handlers=Object.create(null),this._root=t._root||this,this._yield=t._yield,this._torndown=!1,this._fragment=q(this._state,this),t.target&&this._fragment.mount(t.target,null)}function I(t,e){function n(){r=!0,e._set({answer:i.value}),r=!1}function o(t){var n=e.get();e.fire("change",n.answer)}var a,r=!1,i=f("textarea");return i.placeholder=a=t.caption,m(i,"input",n),m(i,"input",o),i.value=t.answer,{mount:function(t,e){u(i,t,e)},update:function(t,e){a!==(a=e.caption)&&(i.placeholder=a),r||(i.value=e.answer)},unmount:function(){c(i)},destroy:function(){g(i,"input",n),g(i,"input",o)}}}function O(t){t=t||{},this._state=i(ut.data(),t.data),this._observers={pre:Object.create(null),post:Object.create(null)},this._handlers=Object.create(null),this._root=t._root||this,this._yield=t._yield,this._torndown=!1,this._fragment=I(this._state,this),t.target&&this._fragment.mount(t.target,null)}function T(t,e,n,o){(o||"state"in e&&y(t.state,n.state))&&(t.delugeClass=e.delugeClass=ct.computed.delugeClass(t.state),t.delugeHeaderClass=e.delugeHeaderClass=ct.computed.delugeHeaderClass(t.state),t.delugeBodyClass=e.delugeBodyClass=ct.computed.delugeBodyClass(t.state))}function E(t,e){function n(t){e.toggle()}function o(t){return"Voted"===t.state?P:"Pending "==t.state?R:"NotVoted"===t.state?F:"boolean"==typeof t.state?V:null}var a,r,i,l=f("div");l.className=a=t.delugeClass;var d=f("div");s(d,l),d.className=r=t.delugeHeaderClass,m(d,"click",n);var p="Initial"===t.state&&L(t,e);p&&p.mount(d,null);var v=h("\n\n        ");s(v,d);var y=f("span");s(y,d),y.className="deluge-helpful",s(h("Was this page helpful?"),y),s(h("\n\n    "),d);var _="Initial"!==t.state&&D(t,e);_&&_.mount(d,null),s(h("\n\n    "),l);var b=f("div");s(b,l),b.className=i=t.delugeBodyClass;var w=o(t),C=w&&w(t,e);C&&C.mount(b,null);var x=h("\n\n    ");s(x,b);var k="Initial"!==t.state&&z(t,e);return k&&k.mount(b,null),{mount:function(t,e){u(l,t,e)},update:function(t,n){a!==(a=n.delugeClass)&&(l.className=a),r!==(r=n.delugeHeaderClass)&&(d.className=r),"Initial"===n.state?p||(p=L(n,e)).mount(d,v):p&&(p.unmount(),p.destroy(),p=null),"Initial"!==n.state?_||(_=D(n,e)).mount(d,null):_&&(_.unmount(),_.destroy(),_=null),i!==(i=n.delugeBodyClass)&&(b.className=i),w===(w=o(n))&&C?C.update(t,n):(C&&(C.unmount(),C.destroy()),(C=w&&w(n,e))&&C.mount(b,x)),"Initial"!==n.state?k?k.update(t,n):(k=z(n,e)).mount(b,null):k&&(k.unmount(),k.destroy(),k=null)},unmount:function(){c(l),p&&p.unmount(),_&&_.unmount(),k&&k.unmount()},destroy:function(){g(d,"click",n),p&&p.destroy(),_&&_.destroy(),C&&(C.unmount(),C.destroy()),k&&k.destroy()}}}function L(t,e){var n=f("span");return n.className="fa fa-comments deluge-comment-icon",{mount:function(t,e){u(n,t,e)},unmount:function(){c(n)},destroy:r}}function D(t,e){var n=f("span");return n.className="fa fa-angle-down deluge-close-icon",{mount:function(t,e){u(n,t,e)},unmount:function(){c(n)},destroy:r}}function A(t,e){var n=f("li");return s(h("We're sorry! Please help us improve this page."),n),{mount:function(t,e){u(n,t,e)},unmount:function(){c(n)},destroy:r}}function H(t,e,n,o,a){function r(t,e,n,o){return"binary"===n.type?B:"freeform"===n.type?Q:null}var i=f("li"),s=r(t,e,n,o),l=s&&s(t,e,n,o,a);return l&&l.mount(i,null),{mount:function(t,e){u(i,t,e)},update:function(t,e,n,o,u){s===(s=r(e,n,o,u))&&l?l.update(t,e,n,o,u):(l&&(l.unmount(),l.destroy()),(l=s&&s(e,n,o,u,a))&&l.mount(i,null))},unmount:function(){c(i)},destroy:function(){l&&(l.unmount(),l.destroy())}}}function B(t,e,n,o,a){var r=new N({target:null,_root:a._root,data:{name:n.name,caption:n.caption}});return r.on("change",function(t){var e=this._context.each_block_value[this._context.question_index];a.update(e.name,t)}),r._context={each_block_value:e,question_index:o},{mount:function(t,e){r._fragment.mount(t,e)},update:function(t,e,n,o,a){r._context.each_block_value=n,r._context.question_index=a;var i={};"questions"in t&&(i.name=o.name),"questions"in t&&(i.caption=o.caption),Object.keys(i).length&&r.set(i)},unmount:function(){r._fragment.unmount()},destroy:function(){r.destroy(!1)}}}function Q(t,e,n,o,a){var r=new O({target:null,_root:a._root,data:{name:n.name,caption:n.caption}});return r.on("change",function(t){var e=this._context.each_block_value[this._context.question_index];a.update(e.name,t)}),r._context={each_block_value:e,question_index:o},{mount:function(t,e){r._fragment.mount(t,e)},update:function(t,e,n,o,a){r._context.each_block_value=n,r._context.question_index=a;var i={};"questions"in t&&(i.name=o.name),"questions"in t&&(i.caption=o.caption),Object.keys(i).length&&r.set(i)},unmount:function(){r._fragment.unmount()},destroy:function(){r.destroy(!1)}}}function P(t,e){var n=f("p");return s(h("Thank you for your feedback!"),n),{mount:function(t,e){u(n,t,e)},update:r,unmount:function(){c(n)},destroy:r}}function R(t,e){var n=f("p");return s(h("Submitting feedback..."),n),{mount:function(t,e){u(n,t,e)},update:r,unmount:function(){c(n)},destroy:r}}function F(t,e){function n(t){e.rate(!0)}function o(t){e.rate(!1)}var a=f("a");a.className="deluge-vote-button",m(a,"click",n),s(h("Yes"),a);var i=h("\n        "),l=f("a");return l.className="deluge-vote-button",m(l,"click",o),s(h("No"),l),{mount:function(t,e){u(a,t,e),u(i,t,e),u(l,t,e)},update:r,unmount:function(){c(a),c(i),c(l)},destroy:function(){g(a,"click",n),g(l,"click",o)}}}function V(t,e){function n(t){e.toggle()}function o(t){e.submit()}var a=f("div");a.className="deluge-questions";var r=f("ul");s(r,a),v(r,"ref",!0);var i=!1===t.state&&A(t,e);i&&i.mount(r,null);var l=p();s(l,r);for(var y=t.questions,_=[],b=0;b<y.length;b+=1)_[b]=H(t,y,y[b],b,e),_[b].mount(r,null);s(h("\n\n            "),a);var w=f("div");s(w,a),w.className="deluge-button-group";var C=f("button");s(C,w),m(C,"click",n),s(h("Cancel"),C),s(h("\n                "),w);var x=f("button");return s(x,w),x.className="primary",m(x,"click",o),s(h("Submit"),x),{mount:function(t,e){u(a,t,e)},update:function(t,n){!1===n.state?i||(i=A(n,e)).mount(r,l):i&&(i.unmount(),i.destroy(),i=null);var o=n.questions;if("questions"in t){for(var a=0;a<o.length;a+=1)_[a]?_[a].update(t,n,o,o[a],a):(_[a]=H(n,o,o[a],a,e),_[a].mount(r,null));for(;a<_.length;a+=1)_[a].unmount(),_[a].destroy();_.length=o.length}},unmount:function(){c(a),i&&i.unmount();for(var t=0;t<_.length;t+=1)_[t].unmount()},destroy:function(){i&&i.destroy(),d(_,!1,0),g(C,"click",n),g(x,"click",o)}}}function z(t,e){function n(t){e.showCollectorDialog()}var o,a=f("a");return a.className="deluge-fix-button jira-link jirafeedback",a.target="_blank",a.title=o="Report a problem with "+t.pagename+" on Jira",m(a,"click",n),s(h("Fix This Page"),a),{mount:function(t,e){u(a,t,e)},update:function(t,e){o!==(o="Report a problem with "+e.pagename+" on Jira")&&(a.title=o)},unmount:function(){c(a)},destroy:function(){g(a,"click",n)}}}function K(t){t=t||{},this._state=i(ct.data(),t.data),T(this._state,this._state,{},!0),this._observers={pre:Object.create(null),post:Object.create(null)},this._handlers=Object.create(null),this._root=t._root||this,this._yield=t._yield,this._torndown=!1,this._renderHooks=[],this._fragment=E(this._state,this),t.target&&this._fragment.mount(t.target,null),this._flush()}function U(t,e){var n=[];return e.forEach(function(t,e){n.push(encodeURIComponent(e)+"="+encodeURIComponent(JSON.stringify(t)))}),t+"?"+n.join("&")}function M(){var t=document.querySelector(".body").getAttribute("data-pagename");if(!Object.prototype.hasOwnProperty.call(ft,t)){var e=document.getElementById("rating-panel");e&&(e.innerText="",e&&new lt(dt,t,e).askFreeformQuestion("reason","What were you looking for?").askQuestion("findability","Did you find it?").askQuestion("accuracy","Was the information you found <strong>accurate</strong>?").askQuestion("clarity","Was the information <strong>clear</strong>?").askQuestion("fragmentation","Was the information you needed <strong>all on one page</strong>?"))}}function W(){dt=document.body.getAttribute("data-project")}function J(){void 0!==window.localStorage&&M()}function G(t){return t.hasClass("current")}function X(){var t=$(".sidebar a.current");(e(t)||n(t)||G(t))&&t.parent("li").addClass("selected-item"),t.parents("ul").each(function(t,e){$(e).css("display","block")}),$(".sphinxsidebarwrapper > ul li:not(.current) > ul:not(.current)").hide(),$(".sphinxsidebarwrapper").show(),$(".sphinxsidebarwrapper .toctree-l1").on("click","a",function(o){var a=$(o.currentTarget);e(a)||!a.parent().hasClass("selected-item")&&n(a)||(o.preventDefault(),a.parent().hasClass("current")?(a.parent().removeClass("current selected-item"),a.siblings("ul").slideUp()):(t.parent().removeClass("selected-item"),t.parents().add(t.siblings("ul")).each(function(t,e){var n=$(e);n.has(o.currentTarget).length||(n.is("ul")?n.removeClass("current").slideUp():n.removeClass("current"))}),a.parent().addClass("current"),a.siblings("ul").slideDown(function(){(e(a)||n(a)||G(t))&&a.parent("li").addClass("selected-item")}),t=a))}),$(".sphinxsidebarwrapper > ul ul a.reference").prepend(function(t){var n=$('<span class="expand-icon"></span>');return e($(this))||n.addClass("docs-expand-arrow"),n})}function Y(t){"#"===t.charAt(0)&&(t=t.substring(1)),$(".tab-content").children().hide(),$(".tabs ."+t).show()}function Z(t){var e=$('a[href="'+t+'"]'),n=e.parent("li"),o=n.parent("ul"),a=$(".nav.nav-tabs.nav-justified .dropdown-toggle"),r=$(".nav.nav-tabs.nav-justified .dropdown");o.hasClass("dropdown-menu")?(a.text(""+e.first().text()).append('<span class="caret"></span>'),r.addClass("active").siblings().removeClass("active")):(n.addClass("active").siblings().removeClass("active"),a.text("Other ").append('<span class="caret"></span>'))}function tt(){var t=$(".nav.nav-tabs.nav-justified"),e=t.first();t.slice(1).detach(),e.detach().insertAfter("h1").first()}function et(){tt();var t=null;if(localStorage.getItem("languagePref"))t=localStorage.getItem("languagePref"),$('a[href="'+t+'"]').length<1&&document.querySelector(".nav.nav-tabs.nav-justified > li:first-child > a")&&(t=document.querySelector(".nav.nav-tabs.nav-justified > li:first-child > a").getAttribute("href"));else{var e=document.querySelector(".nav-tabs > .active > [href]");if(!e)return;t=e.getAttribute("href")}Y(t),Z(t);for(var n=document.querySelectorAll(".nav.nav-tabs.nav-justified a"),o=0;o<n.length;o+=1)!function(t){var e=n[t];e.onclick=function(t){var n=e.getAttribute("href");n&&(localStorage.setItem("languagePref",n),Y(n),Z(n),tt(),t.preventDefault())}}(o)}function nt(t){var e=document.getElementsByClassName("body")[0].getAttribute("data-pagename");return"index"===e?e="":e&&(e+="/"),"/"+t+"/"+e}function ot(){$(".version-selector").on("click",function(t){t.preventDefault();var e=$(t.currentTarget).data("path");window.location.href=nt(e)})}var at=Object.freeze({setup:t}),rt=Object.freeze({setup:a}),it={get:b,fire:w,observe:C,on:x,set:k,_flush:j},st=function(){return{data:function(){return{name:"",caption:"",answer:null}},methods:{change:function(t){this.set({answer:t}),this.fire("change",t)}},computed:{upvoteSelected:function(t){return!0===t?"selected":""},downvoteSelected:function(t){return!1===t?"selected":""}}}}();i(N.prototype,st.methods,it),N.prototype._set=function(t){var e=this._state;this._state=i({},e,t),S(this._state,t,e,!1),_(this,this._observers.pre,t,e),this._fragment.update(t,this._state),_(this,this._observers.post,t,e)},N.prototype.teardown=N.prototype.destroy=function(t){this.fire("destroy"),!1!==t&&this._fragment.unmount(),this._fragment.destroy(),this._fragment=null,this._state={},this._torndown=!0};var ut=function(){return{data:function(){return{name:"",caption:"",answer:""}},methods:{change:function(){this.fire("change",this.get("answer"))}}}}();i(O.prototype,ut.methods,it),O.prototype._set=function(t){var e=this._state;this._state=i({},e,t),_(this,this._observers.pre,t,e),this._fragment.update(t,this._state),_(this,this._observers.post,t,e)},O.prototype.teardown=O.prototype.destroy=function(t){this.fire("destroy"),!1!==t&&this._fragment.unmount(),this._fragment.destroy(),this._fragment=null,this._state={},this._torndown=!0};var ct=function(){function t(t){var e=document.createElement("script");e.type="application/javascript",e.src=t,document.body.appendChild(e)}return{data:function(){return{project:"",pagename:"",state:"Initial",jiraurl:"https://jira.mongodb.org/s/en_UScn8g8x/782/6/1.2.5/_/download/batch/com.atlassian.jira.collector.plugin.jira-issue-collector-plugin:issuecollector-embededjs/com.atlassian.jira.collector.plugin.jira-issue-collector-plugin:issuecollector-embededjs.js?collectorId=298ba4e7",questions:[],answers:{}}},computed:{delugeClass:function(t){return"Initial"===t?"deluge":"deluge deluge-expanded"},delugeHeaderClass:function(t){return"Initial"===t?"deluge-header":"deluge-header deluge-header-expanded"},delugeBodyClass:function(t){return"Initial"===t?"deluge-body":"deluge-body deluge-body-expanded"}},methods:{open:function(){"Initial"===this.get("state")&&(this.set({answers:{}}),this.set({state:"NotVoted"}))},toggle:function(){this.set({answers:{}}),"Initial"===this.get("state")?this.set({state:"NotVoted"}):this.set({state:"Initial"})},submit:function(){var t=this.get("state");if("boolean"!=typeof t)throw new Error("Assertion failed: Feedback submitted without vote");for(var e=new Map,n=this.get("answers"),o=0,a=Object.keys(n);o<a.length;o+=1){var r=a[o],i=n[r];null!==i&&void 0!==i&&e.set(r,i)}this.set({state:"Pending"}),this.fire("submit",{vote:t,fields:e})},rate:function(t){this.set({state:t})},addQuestion:function(t,e,n){return this.set({questions:this.get("questions").concat({type:t,name:e,caption:n})}),this},update:function(t,e){this.get("answers")[t]=e},showCollectorDialog:function(){var e=this;if(window.ATL_JQ_PAGE_PROPS={triggerFunction:function(t){window.setTimeout(function(){return t()},1)},fieldValues:{summary:'Comment on: "'+this.get("project")+"/"+this.get("pagename")+'"'}},window.jQuery)t(this.get("jiraurl"));else{var n=document.createElement("script");n.type="application/javascript",n.integrity="sha256-BbhdlvQf/xTY9gja0Dq3HiwQF8LaCRTXxZKRutelT44=",n.setAttribute("crossorigin","anonymous"),n.src="https://code.jquery.com/jquery-2.2.4.min.js",n.onload=function(){t(e.get("jiraurl"))},document.body.appendChild(n)}}}}}();i(K.prototype,ct.methods,it),K.prototype._set=function(t){var e=this._state;this._state=i({},e,t),T(this._state,t,e,!1),_(this,this._observers.pre,t,e),this._fragment.update(t,this._state),_(this,this._observers.post,t,e),this._flush()},K.prototype.teardown=K.prototype.destroy=function(t){this.fire("destroy"),!1!==t&&this._fragment.unmount(),this._fragment.destroy(),this._fragment=null,this._state={},this._torndown=!0};var lt=function(t,e,n){var o=this;this.project=t,this.path=e,this.storageKey="feedback-"+t+"/"+e;var a=localStorage[this.storageKey],r=a?Date.parse(a).valueOf():-1/0,i="Initial";(new Date).valueOf()<r+2592e6&&(i="Voted"),this.app=new K({target:n,data:{state:i,project:t,pagename:e}}),this.app.on("submit",function(t){o.sendRating(t.vote,t.fields).then(function(){o.app.set({state:"Voted"})})})};lt.prototype.askQuestion=function(t,e){return this.app.addQuestion("binary",t,e),this},lt.prototype.askFreeformQuestion=function(t,e){return this.app.addQuestion("freeform",t,e),this},lt.prototype.sendRating=function(t,e){var n=this;return new Promise(function(o,a){e.set("v",t),e.set("p",n.project+"/"+n.path);var r=U("http://deluge.us-east-1.elasticbeanstalk.com/",e),i=new Image;i.onload=function(){return o()},i.onerror=function(){return a()},i.src=r})},lt.prototype.open=function(){this.app.open()};var dt=null,ft={"meta/404":!0,search:!0},ht=Object.freeze({init:W,setup:J}),pt=Object.freeze({setup:X}),mt=Object.freeze({setup:et}),gt=Object.freeze({setup:ot}),vt=function(){this.components=[]};vt.prototype.register=function(t){this.components.push(t),t.init&&t.init()},vt.prototype.update=function(){for(var t=this,e=0,n=t.components;e<n.length;e+=1)n[e].setup(t)};var yt=new vt;$(function(){function t(){location.hash&&document.getElementById(location.hash.substr(1))&&$(window).scrollTop(window.scrollY-75)}yt.register(at),yt.register(rt),yt.register(ht),yt.register(pt),yt.register(mt),yt.register(gt),$("body").on("click","#header-db, .sidebar, .content",function(t){$(".option-popup").addClass("closed").find(".fa-angle-down, .fa-angle-up").removeClass("fa-angle-down").addClass("fa-angle-up")}),$(".sphinxsidebarwrapper h3 a.version").on("click",function(t){t.preventDefault(),t.stopPropagation(),$(".option-popup").removeClass("closed")}),$(".toc > ul > li > ul > li").length||$(".right-column .toc").hide(),$(".expand-toc-icon").on("click",function(t){t.preventDefault(),$(".sidebar").toggleClass("reveal")});var e=$(window),n=$(".sidebar"),o=e.width()<=1093;if(e.resize(function(t){o&&e.width()>1093?(o=!1,n.removeClass("reveal")):!o&&e.width()<=1093&&(o=!0)}),window.addEventListener("hashchange",t),location.hash&&window.setTimeout(t,10),$(".content").on("click","a",function(e){$(e.currentTarget).attr("href")===location.hash&&window.setTimeout(t,10)}),yt.update(),document.querySelector){var a=document.querySelector("a.current");a&&a.scrollIntoView(!1)}})}();
//# sourceMappingURL=navbar.js.map
