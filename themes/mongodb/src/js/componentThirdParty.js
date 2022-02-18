const ENABLED_SITES_FOR_DELIGHTED = new Set(['docs', 'guides', 'manual']);

export function initialize() {
    /* eslint-disable */

    // Delighted
    !function(e,t,r,n,a){if(!e[a]){for(var i=e[a]=[],s=0;s<r.length;s++){var c=r[s];i[c]=i[c]||function(e){return function(){var t=Array.prototype.slice.call(arguments);i.push([e,t])}}(c)}i.SNIPPET_VERSION="1.0.1";var o=t.createElement("script");o.type="text/javascript",o.async=!0,o.src="https://d2yyd1h5u9mauk.cloudfront.net/integrations/web/v1/library/"+n+"/"+a+".js";var l=t.getElementsByTagName("script")[0];l.parentNode.insertBefore(o,l)}}(window,document,["survey","reset","config","init","set","get","event","identify","track","page","screen","group","alias"],"Dk30CC86ba0nATlK","delighted");
}

export function setup(fastNav) {
    const project = document.body.getAttribute('data-project');
    const branch = document.body.getAttribute('data-branch');

    try {
        const isStaging = window.location.origin === "https://docs-mongodbcom-staging.corp.mongodb.com";
        if (!isStaging && ENABLED_SITES_FOR_DELIGHTED.has(project)) {
            const projectName = project === 'docs' ? 'manual' : project;
            window.delighted.survey({
                minTimeOnPage: 90,
                properties: {
                    branch,
                    project: projectName,
                }
            });
        }
    } catch (err) {
        console.error(err);
    }

    // Update our path. We're not using Gatsby, but this is the event name that was already in use.
    try {
        window.dataLayer.push({event: 'gatsby-route-change'});
    } catch (err) {
        console.error('Error updating route:', err);
    }
}
