import {reportAnalytics} from './util';

function reportClick(anchorElement) {
    reportAnalytics('Link Clicked', {
        'text': anchorElement.text,
        'href': anchorElement.href
    });
}

export function setup() {
    // only on ecosystem homepage, track link clicks
    if (document.body.dataset && document.body.dataset.project === 'ecosystem' && (window.location.href === 'https://docs.mongodb.com/ecosystem/' || window.location.href === 'https://docs.mongodb.com/ecosystem/drivers/')) {
        // get links on ecosystem
        const anchors = document.querySelectorAll('a.external');
        for (let i = 0; i < anchors.length; i += 1) {
            const anchor = anchors[i];
            anchor.addEventListener('click', reportClick.bind(this, anchor));
        }
    }
}
