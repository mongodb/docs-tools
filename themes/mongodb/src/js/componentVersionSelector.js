function fullDocsPath(base) {
    const body = document.getElementsByClassName('body')[0];
    let path = body.getAttribute('data-pagename');

    // skip if pagename is undefined (index.html)
    if (path === 'index') {
        path = '';
    } else if (path) {
        path = `${path}/`;
    }

    return `/${base}/${path}`;
}

export function setup() {
    $('.version-selector').on('click', (e) => {
        e.preventDefault();
        const base = $(e.currentTarget).data('path');
        window.location.href = fullDocsPath(base);
    });
}
