import {MarianUI} from './Marian.js';
import NavbarDropdown from './navbar-dropdown.js';
import PropTypes from 'prop-types';
import Velocity from 'velocity-animate';
import classNames from 'classnames';
import preact from 'preact';

function DownloadArrowIcon() {
    return (<svg height="11" width="9" xmlns="http://www.w3.org/2000/svg"><path d="m8.8 6.8-1.2-1.2-2.1 2v-7.6h-1.7v7.6l-2.1-2-1.2 1.2 4.2 4.2z" fill="#69b241"/></svg>);
}

class Navbar extends preact.Component {
    constructor (props) {
        super(props);
        this.state = JSON.parse(props.navprops);
        this.state.enableMarian = Boolean(document.body.getAttribute('data-enable-marian'));

        // There are four supported configurations:
        // 1) No Marian
        // 2) data-project-title & data-search-properties are set
        // 3) data-project-title & data-search-properties are empty
        // 4) data-search-properties is not set, but data-project and data-branch are

        if (this.state.enableMarian) {
            let label = document.body.getAttribute('data-project-title');
            let searchProperties = document.body.getAttribute('data-search-properties');
            if (searchProperties === null) {
                const projectName = document.body.getAttribute('data-project');
                const projectBranch = document.body.getAttribute('data-branch');
                searchProperties = `${projectName}-${projectBranch}`;

                if (label) {
                    if (projectBranch && projectBranch !== 'master') {
                        label += ` ${projectBranch}`;
                    }
                }
            }

            this.state.marian = new MarianUI(searchProperties, label, (newQuery) => {
                this.setState({
                    'searchText': newQuery
                });

                this.search();
            });
            this.state.timeout = -1;
            this.state.searchText = this.state.marian.query;

            window.history.onnavigate = () => {
                this.setState({
                    'searchText': ''
                });
                this.search();
            };
        }

        this.calculateBlurredWidth = this.calculateBlurredWidth.bind(this);
        this.calculateFocusWidth = this.calculateFocusWidth.bind(this);
        this.animateSearch = this.animateSearch.bind(this);

        this.onInput = this.onInput.bind(this);
    }

    onInput (event) {
        if (!this.state.enableMarian) { return; }

        this.setState({
            'searchText': event.target.value
        });

        window.clearTimeout(this.state.timeout);
        this.setState({'timeout':
            window.setTimeout(() => {
                this.search();
            }, 250)});
    }

    search () {
        if (!this.state.enableMarian) { return; }

        window.clearTimeout(this.state.timeout);
        this.state.marian.search(this.state.searchText);
    }

    componentDidMount () {
        // Pass the animateSearch function
        const animateSearch = this.animateSearch;

        if (this.state.enableMarian) {
            const input = document.querySelector('.navbar-search');
            animateSearch(input);

            return;
        }
    }

    // Animate the search bar on focus, blur and window resize
    animateSearch (input) {
        const calculateBlurredWidth = this.calculateBlurredWidth;
        const calculateFocusWidth = this.calculateFocusWidth;

        // Set the initial size of the search bar depending on browser size
        input.style.width = calculateBlurredWidth();

        // Width of the search bar must be set manually when in or out of focus
        input.onfocus = function() {
            // Stop any executing animations, then start expanding
            Velocity(input, 'stop');
            Velocity(input, {'width': calculateFocusWidth()}, {'duration': 200});
        };

        input.onblur = function() {
            // Stop any executing animations, then start collapsing
            Velocity(input, 'stop');
            Velocity(input, {'width': calculateBlurredWidth()}, {'duration': 200});
        };

        // Resize search bar when the browser is resized
        window.addEventListener('resize', () => {
            document.querySelector('.navbar-search').style.width = calculateBlurredWidth();
        });
    }

    // Calculates the size of the search bar when it's not in focus
    calculateBlurredWidth () {
        const totalWidth = document.querySelector('.navbar__right').clientWidth;
        const linksWidth = document.querySelector('.navbar-links').clientWidth;
        const downloadWidth = document.querySelector('.navbar-download').clientWidth;

        const searchWidth = totalWidth - (linksWidth + downloadWidth);

        // Return as a string to forcefeed to velocity.js
        return `${searchWidth}px`;
    }

    // Calculates the size of the search bar when it's in focus, cursor
    calculateFocusWidth () {
        return `${document.querySelector('.navbar__right').clientWidth}px`;
    }

    render () {
        let searchBar = null;
        if (this.state.enableMarian) {
            searchBar = <input type="search"
                className="navbar-search"
                onInput={this.onInput}
                value={this.state.searchText}
                placeholder="Search Documentation"
                aria-label="Search Documentation"></input>;
        }

        const linkElements = this.state.links.map((link, i) => {
            const linkClass = classNames({
                'navbar-links__item': true,
                'navbar-links__item--active': link.active
            });

            return <a href={ link.url } key={i} className={ linkClass }>{ link.text }</a>;
        });

        return (
            <nav className="navbar">
                <div className="navbar__left">
                    <a href="https://www.mongodb.com/">
                        <img src="https://docs.mongodb.com/images/mongodb-logo.svg" className="navbar-brand" alt="MongoDB Logo" />
                    </a>

                    <span className="navbar-seperator"></span>

                    <NavbarDropdown links={this.state.dropdown} />
                </div>

                <div className="navbar__right">
                    <div className="navbar-links">
                        { linkElements }
                    </div>

                    <div className="navbar-download">
                        <a href="https://www.mongodb.com/download-center?jmp=tutorials" className="navbar-download__text">Download MongoDB</a>
                        <DownloadArrowIcon />
                    </div>
                    { searchBar }
                </div>
            </nav>
        );
    }
}

Navbar.propTypes = {
    'navprops': PropTypes.objectOf(PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)))
};

const navbar = document.getElementById('navbar');
preact.render(<Navbar {...(navbar.dataset)} />, navbar);
