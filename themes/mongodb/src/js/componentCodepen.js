export function setup() {
    const codepenBlocks = document.getElementsByClassName('codepen');
    if (codepenBlocks.length) {
        const codepenScript = document.createElement('script');
        codepenScript.src = 'https://production-assets.codepen.io/assets/embed/ei.js';
        document.body.appendChild(codepenScript);
    }
}
