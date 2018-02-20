export function setup() {
    const codepenBlocks = document.getElementsByClassName('codepen');
    if (codepenBlocks.length) {
        const codepenScript = document.createElement('script');
        codepenScript.src = 'https://production-assets.codepen.io/assets/embed/ei.js';
        codepenScript.async = true;
        document.body.appendChild(codepenScript);
    }
}
