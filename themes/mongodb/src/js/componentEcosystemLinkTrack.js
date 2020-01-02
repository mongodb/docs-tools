import {reportAnalytics, toArray} from './util';

export function setup() {
    // only on ecosystem homepage, track link clicks
    if (document.body.dataset && document.body.dataset.project === 'ecosystem' && window.location.href === 'https://docs.mongodb.com/ecosystem/') {
        // get links on ecosystem
        const anchors = toArray(document.getElementsByTagName('a'));
        anchors.forEach(function(anchorElement) {
            anchorElement.addEventListener('click', reportAnalytics('Link Clicked', {
                'text': anchorElement.text,
                'href': anchorElement.href
            }));
        });
    }
}
