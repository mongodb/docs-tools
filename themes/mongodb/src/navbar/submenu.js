import PropTypes from 'prop-types';
import classNames from 'classnames';
import preact from 'preact';

class Submenu extends preact.Component {
    constructor(props) {
        super(props);
        this.state = {
            'open': props.open
        };

        this.toggle = this.toggle.bind(this);
    }

    toggle(event) {
        this.setState({
            'open': !this.state.open
        });
    }

    render() {
        const titleClass = classNames({
            'submenu__title': true,
            'submenu__title--open': this.state.open
        });

        const submenuClass = classNames({
            'submenu': true,
            'submenu--hidden': !this.state.open,
            'submenu--shown': this.state.open
        });

        return (
            <div>
                <span className={titleClass} onClick={this.toggle}>
                    {this.props.title}
                </span>
                <ul className={ submenuClass }>{ this.props.children }</ul>
            </div>
        );
    }
}

Submenu.propTypes = {
    'open': PropTypes.bool,
    'title': PropTypes.string,
    'children': PropTypes.arrayOf(PropTypes.node)
};

export default Submenu;
