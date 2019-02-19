import PropTypes from 'prop-types';
import preact from 'preact';

class FreeformQuestion extends preact.Component {
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
        const {errorText, placeholder} = this.props;
        const {error, text} = this.state;
        return (
            <div>
                <textarea
                    placeholder={placeholder}
                    onInput={this.handleChange}
                    value={text}></textarea>
                <div
                    className="error"
                    style={{'visibility': error ? 'visible' : 'hidden'}}>
                    {errorText}
                </div>
            </div>
        );
    }
}

FreeformQuestion.propTypes = {
    'errorText': PropTypes.string,
    'hasError': PropTypes.func,
    'placeholder': PropTypes.string,
    'store': PropTypes.objectOf(PropTypes.func).isRequired
};

FreeformQuestion.defaultProps = {
    'hasError': () => false
};

export default FreeformQuestion;
