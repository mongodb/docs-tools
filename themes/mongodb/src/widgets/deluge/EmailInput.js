import PropTypes from 'prop-types';
import preact from 'preact';

const ERROR_TEXT = 'Please enter a valid email address.';

class EmailInput extends preact.Component {
    constructor(props) {
        super(props);

        this.state = {
            'error': false,
            'text': ''
        };

        this.handleChange = this.handleChange.bind(this);
    }

    handleChange(e) {
        const {store} = this.props;
        const value = e.target.value;

        if (value === '' || this.emailIsValid(value)) {
            store.set(value);
            this.setState({
                'error': false,
                'text': value
            });
        } else {
            store.set('');
            this.setState({
                'error': true,
                'text': value
            });
        }
    }

    emailIsValid(email) {
        return (/^[^\s@]+@[^\s@]+\.[^\s@]+$/).test(email);
    }

    render() {
        const {placeholder} = this.props;
        const {error, text} = this.state;
        return (
            <div>
                <input
                    onInput={this.handleChange}
                    placeholder={placeholder}
                    type="email"
                    value={text} />
                <div className="error" style={{'visibility': error ? 'visible' : 'hidden'}}>
                    {ERROR_TEXT}
                </div>
            </div>
        );
    }
}

EmailInput.propTypes = {
    'placeholder': PropTypes.string,
    'store': PropTypes.objectOf(PropTypes.func).isRequired
};

export default EmailInput;
