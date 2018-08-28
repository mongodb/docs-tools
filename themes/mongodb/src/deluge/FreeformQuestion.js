import PropTypes from 'prop-types';
import preact from 'preact';

export default function FreeformQuestion({placeholder, store}) {
    return (
        <textarea
            placeholder={placeholder}
            onChange={(ev) => store.set(ev.target.value)}
            value={store.get() || ''}></textarea>
    );
}

FreeformQuestion.propTypes = {
    'placeholder': PropTypes.string,
    'store': PropTypes.objectOf(PropTypes.func).isRequired
};
