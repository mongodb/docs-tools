export function setup() {
    const showNavButton = document.getElementById('showNav');
    if (showNavButton) {
        showNavButton.onclick = () => {
            document.getElementById('sphinxsidebar').style.display = 'block';
            document.getElementById('left-column').style.display = 'flex';
            document.getElementById('showNav').style.display = 'none';
        };
    }

    const closeNavButton = document.getElementById('closeNav');
    if (closeNavButton) {
        closeNavButton.onclick = () => {
            document.getElementById('showNav').style.display = 'flex';
            document.getElementById('left-column').style.display = 'none';
        };
    }
}
