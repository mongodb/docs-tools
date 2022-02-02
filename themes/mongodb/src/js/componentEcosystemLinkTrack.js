import {reportAnalytics} from './util';

function reportClick(anchorElement) {
    reportAnalytics('Link Clicked', {
        'text': anchorElement.text,
        'href': anchorElement.href
    });
}

export function setup() {
    // only on ecosystem homepage, track link clicks
    const driversUrls = ['https://docs.mongodb.com/drivers/', 'https://www.mongodb.com/docs/drivers/'];
    if (document.body.dataset && document.body.dataset.project === 'ecosystem' && driversUrls.includes(window.location.href)) {
        // get links on ecosystem
        const anchors = document.querySelectorAll('a.external');
        for (let i = 0; i < anchors.length; i += 1) {
            const anchor = anchors[i];
            anchor.addEventListener('click', reportClick.bind(this, anchor));
        }
    }
}
