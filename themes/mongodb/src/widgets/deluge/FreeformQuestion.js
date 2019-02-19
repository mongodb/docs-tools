import PropTypes from 'prop-types';
import preact from 'preact';

const MIN_CHAR_COUNT = 15;
const ERROR_TEXT = `Please respond with at least ${MIN_CHAR_COUNT} characters.`;

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
        const {store} = this.props;
        const value = ev.target.value;

        if (value === '' || value.length >= MIN_CHAR_COUNT) {
            this.setState({
                'error': false,
                'text': value
            });
            store.set(value);
            ev.target.setCustomValidity('');
        } else {
            this.setState({
                'error': true,
                'text': value
            });
            store.set('');
            ev.target.setCustomValidity(ERROR_TEXT);
        }
    }

    render() {
        const {placeholder} = this.props;
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
                    {ERROR_TEXT}
                </div>
            </div>
        );
    }
}

FreeformQuestion.propTypes = {
    'placeholder': PropTypes.string,
    'store': PropTypes.objectOf(PropTypes.func).isRequired
};

export default FreeformQuestion;
