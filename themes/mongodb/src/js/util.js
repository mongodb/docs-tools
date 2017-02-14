export function isLeafNode($node) {
    return !$node.siblings('ul:not(.simple)').length;
}

/* Checks a whitelist for non-leaf nodes that should trigger a full page reload */
export function requiresPageload($node) {
    const docsExcludedNav = window.docsExcludedNav;

    if (!docsExcludedNav || !docsExcludedNav.length) {
        return false;
    }

    for (let i = 0; i < docsExcludedNav.length; i += 1) {
        if ($node[0].href.indexOf(docsExcludedNav[i]) !== -1) {
            return true;
        }
    }
    return false;
}
