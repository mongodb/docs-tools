const HTML = `<p class="first admonition-title">AWS USERS</p>
<p class="last">Welcome AWS Users! <a class="reference external" href="https://www.mongodb.com/cloud/atlas?jmp=docs">MongoDB Atlas</a> is
the fully-managed database-as-a-service with all the features and
performance of MongoDB. Atlas runs on AWS, Azure, and GCP. To
explore Atlas, use the promotional code <code class="docutils literal notranslate"><span class="pre">REALMONGO</span></code> for 250 USD of
Atlas credit.</p>`;

export function setup() {
    const newElement = document.createElement('div');
    newElement.className = 'note admonition';
    newElement.innerHTML = HTML;

    let tag = document.getElementsByTagName('h1')[0];
    if (!tag) { return; }

    let mode = 'afterend';
    let next = tag.nextElementSibling;
    if (next && next.id === 'on-this-page') {
        tag = next;
        next = tag.nextElementSibling;
    }

    if (next.querySelector('dl dt .descname') !== null) {
        mode = 'afterbegin';
        tag = next.querySelector('dl dd');
    }

    tag.insertAdjacentElement(mode, newElement);
}
