import Deluge from './deluge/deluge';
import PropTypes from 'prop-types';
import Suggestion from './suggestion/suggestion';
import preact from 'preact';

const whitelist = [
];

class Widgets extends preact.Component {
    constructor(props) {
        super(props);
        this.isSuggestionPage = this.isSuggestionPage(this.props.path);
        this.handleOpenDrawer = this.handleOpenDrawer.bind(this);
        this.handleCloseDrawer = this.handleCloseDrawer.bind(this);

        this.state = {
            'drawerIsOpen': false,
            'drawerHasOpened': false
        };
    }

    isSuggestionPage(path) {
        return whitelist.indexOf(path) >= 0;
    }

    handleOpenDrawer() {
        // Don't display suggestions again after closing
        if (this.state.drawerHasOpened) {
            return;
        }

        this.setState((prevState) => ({
            'drawerIsOpen': true,
            'drawerHasOpened': true
        }));
    }

    handleCloseDrawer() {
        this.setState((prevState) => ({
            'drawerIsOpen': false
        }));
    }

    render() {
        return (
            <div>
                <Deluge
                    project={this.props.project}
                    path={this.props.path}
                    handleOpenDrawer={this.handleOpenDrawer}
                    canShowSuggestions={this.isSuggestionPage}
                />
                {this.isSuggestionPage &&
                    <Suggestion
                        drawerIsOpen={this.state.drawerIsOpen}
                        handleCloseDrawer={this.handleCloseDrawer}
                    />
                }
            </div>
        );
    }
}

Widgets.propTypes = {
    'project': PropTypes.string.isRequired,
    'path': PropTypes.string.isRequired
};

export default function widgets(project, path, rootElement) {
    preact.render('', rootElement, rootElement._widgetsRendered);

    if (path) {
        rootElement._widgetsRendered = preact.render(
            <Widgets project={project} path={path} />,
            rootElement);
    }
}
