import PropTypes from 'prop-types';
import preact from 'preact';

function Menu(props) {
    return (<ul className="menu">
        { props.children }
    </ul>);
}

Menu.propTypes = {
    'children': PropTypes.arrayOf(PropTypes.node)
};

export default Menu;
