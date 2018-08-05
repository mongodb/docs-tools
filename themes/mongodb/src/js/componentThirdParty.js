const SAMPLE_FACTORS = {
    'charts': 0.12158,
    'guides': 0.02644,
    'stitch': 0.03162,
    'docs-ruby': 0.47984,
    'ecosystem': 0.00997,
    'docs-php-library': 0.04165,
    'atlas': 0.01176,
    'compass': 0.01684,
    'manual': 0.00022,
    'landing': 0.00806,
    'mongoid': 0.07576,
    'mms-cloud': 0.06358,
    'mms-onprem': 0.01790,
    'bi-connector': 0.03912,
    'spark-connector': 0.05562
};

// Wait for a property to be attached to the global window
function waitForFunction(propertyName, cb) {
    let totalWaited = 0;
    function f() {
        if (typeof window[propertyName] === 'function') {
            cb(window[propertyName]);
            return;
        }

        if (totalWaited > 5000) {
            console.error(`waitForFunction: timed out waiting for ${propertyName}`);
            return;
        }

        totalWaited += 250;
        setTimeout(f, 250);
        return;
    }

    f();
}

export function initialize() {
    /* eslint-disable */

    // FullStory
    window['_fs_debug'] = false;
    window['_fs_host'] = 'fullstory.com';
    window['_fs_org'] = '54YFM';
    window['_fs_namespace'] = 'FS';
    ;(function(m,n,e,t,l,o,g,y){
        if (e in m && m.console && m.console.log) { m.console.log('FullStory namespace conflict. Please set window["_fs_namespace"].'); return;}
        g=m[e]=function(a,b){g.q?g.q.push([a,b]):g._api(a,b);};g.q=[];
        o=n.createElement(t);o.async=1;o.src='https://'+_fs_host+'/s/fs.js';
        y=n.getElementsByTagName(t)[0];y.parentNode.insertBefore(o,y);
        g.identify=function(i,v){g(l,{uid:i});if(v)g(l,v)};g.setUserVars=function(v){g(l,v)};
        g.identifyAccount=function(i,v){o='account';v=v||{};v.acctId=i;g(o,v)};
        g.clearUserCookie=function(c,d,i){if(!c || document.cookie.match('fs_uid=[`;`]*`[`;`]*`[`;`]*`')){
        d=n.domain;while(1){n.cookie='fs_uid=;domain='+d+
        ';path=/;expires='+new Date(0).toUTCString();i=d.indexOf('.');if(i<0)break;d=d.slice(i+1)}}};
    })(window,document,window['_fs_namespace'],'script','user');

    // Delighted
    !function(e,t,r,n,a){if(!e[a]){for(var i=e[a]=[],s=0;s<r.length;s++){var c=r[s];i[c]=i[c]||function(e){return function(){var t=Array.prototype.slice.call(arguments);i.push([e,t])}}(c)}i.SNIPPET_VERSION="1.0.1";var o=t.createElement("script");o.type="text/javascript",o.async=!0,o.src="https://d2yyd1h5u9mauk.cloudfront.net/integrations/web/v1/library/"+n+"/"+a+".js";var l=t.getElementsByTagName("script")[0];l.parentNode.insertBefore(o,l)}}(window,document,["survey","reset","config","init","set","get","event","identify","track","page","screen","group","alias"],"Dk30CC86ba0nATlK","delighted");

    // Segment
    !function(){var analytics=window.analytics=window.analytics||[];if(!analytics.initialize)if(analytics.invoked)window.console&&console.error&&console.error("Segment snippet included twice.");else{analytics.invoked=!0;analytics.methods=["trackSubmit","trackClick","trackLink","trackForm","pageview","identify","reset","group","track","ready","alias","debug","page","once","off","on"];analytics.factory=function(t){return function(){var e=Array.prototype.slice.call(arguments);e.unshift(t);analytics.push(e);return analytics}};for(var t=0;t<analytics.methods.length;t++){var e=analytics.methods[t];analytics[e]=analytics.factory(e)}analytics.load=function(t,e){var n=document.createElement("script");n.type="text/javascript";n.async=!0;n.src="https://cdn.segment.com/analytics.js/v1/"+t+"/analytics.min.js";var a=document.getElementsByTagName("script")[0];a.parentNode.insertBefore(n,a);analytics._loadOptions=e};analytics.SNIPPET_VERSION="4.1.0";
        analytics.load("aGhVvyxnPWlyP71vVl9ZjGWxAtoVGLXX");
    }}();

    // Google Analytics
    waitForFunction('ga', (ga) => {
        ga('create', 'UA-7301842-14', 'auto');
    });
}

export function setup(fastNav) {
    const project = document.body.getAttribute('data-project');
    const branch = document.body.getAttribute('data-branch');

    try {
        const sampleFactor = SAMPLE_FACTORS[project] || 0.1;
        window.delighted.survey({
            minTimeOnPage: 180,
            sampleFactor: sampleFactor,
            properties: {
              project,
              branch,
            }
        });
    } catch (err) {
        console.error(err);
    }

    // Update Google Analytics
    waitForFunction('ga', (ga) => {
        window.ga('set', 'page', location.pathname);
        window.ga('send', 'pageview');
    });

    // Update Segment
    try {
        window.analytics.page({
          path: location.pathname,
          url: location.href,
          project: project,
          branch: branch
        });
    } catch (err) {
        console.error(err);
    }
}
