export function isLeafNode($node) {
    return !$node.siblings('ul:not(.simple)').length;
}

export function toArray(arrayLike) {
    const result = [];
    for (let i = 0; i < arrayLike.length; i += 1) {
        result.push(arrayLike[i]);
    }

    return result;
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

export function throttle(func, wait) {
    let args = null;
    let result = null;
    let timeout = null;
    let previous = 0;

    function later() {
        previous = Date.now();
        timeout = null;
        result = func.apply(...args);
        if (!timeout) {
            args = null;
        }
    }

    return function(...newArgs) {
        const now = Date.now();
        const remaining = wait - (now - previous);
        args = newArgs;
        if (remaining <= 0 || remaining > wait) {
            if (timeout) {
                window.clearTimeout(timeout);
                timeout = null;
            }

            previous = now;
            result = func(...args);
            if (!timeout) {
                args = null;
            }
        } else if (!timeout) {
            timeout = window.setTimeout(later, remaining);
        }

        return result;
    };
}

export class Dispatcher {
    constructor() {
        this.listeners = [];
    }

    listen(handler) {
        this.listeners.push(handler);
    }

    dispatch(ctx) {
        for (let i = 0; i < this.listeners.length; i += 1) {
            this.listeners[i](ctx);
        }
    }
}
