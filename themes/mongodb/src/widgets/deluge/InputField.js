import PropTypes from 'prop-types';
import preact from 'preact';

class InputField extends preact.Component {
    constructor(props) {
        super(props);

        this.state = {
            'error': false,
            'text': ''
        };

        this.handleChange = this.handleChange.bind(this);
    }

    handleChange(ev) {
        const {hasError, store} = this.props;
        const value = ev.target.value;
        const error = hasError(value);

        if (error) {
            store.set('');
            ev.target.setCustomValidity(error);
        } else {
            store.set(value);
            ev.target.setCustomValidity('');
        }
        this.setState({
            'error': error,
            'text': value
        });
    }

    render() {
        const {errorText, inputType, placeholder} = this.props;
        const {error, text} = this.state;
        return (
            <div>
                <input
                    onInput={this.handleChange}
                    placeholder={placeholder}
                    type={inputType}
                    value={text} />
                <div className="error" style={{'visibility': error ? 'visible' : 'hidden'}}>
                    {errorText}
                </div>
            </div>
        );
    }
}

InputField.propTypes = {
    'errorText': PropTypes.string,
    'hasError': PropTypes.func,
    'inputType': PropTypes.string,
    'placeholder': PropTypes.string,
    'store': PropTypes.objectOf(PropTypes.func).isRequired
};

InputField.defaultProps = {
    'hasError': () => false,
    'inputType': 'text'
};

export default InputField;
