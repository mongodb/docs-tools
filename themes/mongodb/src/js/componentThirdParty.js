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

export function initialize() {
    /* eslint-disable */

    // Delighted
    !function(e,t,r,n,a){if(!e[a]){for(var i=e[a]=[],s=0;s<r.length;s++){var c=r[s];i[c]=i[c]||function(e){return function(){var t=Array.prototype.slice.call(arguments);i.push([e,t])}}(c)}i.SNIPPET_VERSION="1.0.1";var o=t.createElement("script");o.type="text/javascript",o.async=!0,o.src="https://d2yyd1h5u9mauk.cloudfront.net/integrations/web/v1/library/"+n+"/"+a+".js";var l=t.getElementsByTagName("script")[0];l.parentNode.insertBefore(o,l)}}(window,document,["survey","reset","config","init","set","get","event","identify","track","page","screen","group","alias"],"Dk30CC86ba0nATlK","delighted");

    // Segment
    !function(){var analytics=window.analytics=window.analytics||[];if(!analytics.initialize)if(analytics.invoked)window.console&&console.error&&console.error("Segment snippet included twice.");else{analytics.invoked=!0;analytics.methods=["trackSubmit","trackClick","trackLink","trackForm","pageview","identify","reset","group","track","ready","alias","debug","page","once","off","on"];analytics.factory=function(t){return function(){var e=Array.prototype.slice.call(arguments);e.unshift(t);analytics.push(e);return analytics}};for(var t=0;t<analytics.methods.length;t++){var e=analytics.methods[t];analytics[e]=analytics.factory(e)}analytics.load=function(t,e){var n=document.createElement("script");n.type="text/javascript";n.async=!0;n.src="https://cdn.segment.com/analytics.js/v1/"+t+"/analytics.min.js";var a=document.getElementsByTagName("script")[0];a.parentNode.insertBefore(n,a);analytics._loadOptions=e};analytics.SNIPPET_VERSION="4.1.0";
        analytics.load("aGhVvyxnPWlyP71vVl9ZjGWxAtoVGLXX");
    }}();
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
