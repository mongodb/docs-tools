import BinaryQuestion from './BinaryQuestion';
import FreeformQuestion from './FreeformQuestion';
import InputField from './InputField';
import MainWidget from './MainWidget';
import PropTypes from 'prop-types';
import preact from 'preact';

const FEEDBACK_URL = 'http://deluge.us-east-1.elasticbeanstalk.com/';
const MIN_CHAR_COUNT = 15;
const MIN_CHAR_ERROR_TEXT = `Please respond with at least ${MIN_CHAR_COUNT} characters.`;
const EMAIL_ERROR_TEXT = 'Please enter a valid email address.';
const EMAIL_PROMPT_TEXT = 'May we contact you about your feedback?';

// Take a url and a query parameters object, and return the resulting url.
function addQueryParameters(url, parameters) {
    const queryComponents = Object.keys(parameters).map((key) =>
        `${encodeURIComponent(key)}=${encodeURIComponent(JSON.stringify(parameters[key]))}`);
    return `${url}?${queryComponents.join('&')}`;
}

class Deluge extends preact.Component {
    constructor(props) {
        super(props);

        this.state = {
            'answers': {},
            'emailError': false,
            'formLengthError': false,
            'voteAcknowledgement': null
        };

        const crypto = (window.crypto || window.msCrypto);
        if (crypto) {
            const buf = new Uint8Array(16);
            crypto.getRandomValues(buf);
            this.state.voteId = btoa(Array.prototype.map.call(buf,
                (ch) => String.fromCharCode(ch)).join('')).slice(0, -2);
        }

        this.onSubmit = this.onSubmit.bind(this);
        this.onInitialSubmit = this.onInitialSubmit.bind(this);
    }

    onSubmit(vote) {
        const fields = {};

        const answers = this.state.answers;
        const keys = Object.keys(answers);
        for (let i = 0; i < keys.length; i += 1) {
            const key = keys[i];

            // Report booleans and non-empty strings
            if (answers[key] || answers[key] === false) {
                fields[key] = answers[key];
            }
        }

        this.sendRating(vote, fields, null).then(() => {
            this.setState({
                'voteAcknowledgement': (vote) ? 'up' : 'down'
            });
        }).
            catch((err) => {
                console.error(err);
            });
    }

    onInitialSubmit(vote) {
        this.sendRating(vote, {}, 'initial_vote').then(() => {
            this.setState({
                'voteAcknowledgement': (vote) ? 'up' : 'down'
            });
        }).
            catch((err) => {
                console.error(err);
            });
    }

    sendRating(vote, fields, requestPath) {
        const path = `${this.props.project}/${this.props.path}`;

        // Report to Segment
        const analyticsData = {
            'useful': vote,
            ...fields
        };

        try {
            const user = window.analytics.user();
            const segmentUID = user.id();
            if (segmentUID) {
                fields.segmentUID = segmentUID.toString();
            } else {
                fields.segmentAnonymousID = user.anonymousId().toString();
            }
            window.analytics.track('Feedback Submitted', analyticsData);
        } catch (err) {
            console.error(err);
        }

        // Report to Deluge
        return new Promise((resolve, reject) => {
            const feedbackUrl = requestPath ? `${FEEDBACK_URL}${requestPath}` : FEEDBACK_URL;
            const url = addQueryParameters(feedbackUrl, {
                ...fields,
                'v': vote,
                'p': path,
                'vId': this.state.voteId,
                'url': location.href
            });

            // Report this rating using an image GET to work around the
            // same-origin policy
            const img = new Image();
            img.onload = () => resolve();
            img.onerror = () => reject(new Error('Failed to report feedback'));
            img.src = url;
        });
    }

    makeStore(key) {
        return {
            'get': () => this.state.answers[key],
            'set': (val) => this.setState((prevState) => ({
                'answers': {
                    ...prevState.answers,
                    [key]: val
                }
            }))
        };
    }

    validateFormLength(input) {
        const hasError = !(input === '' || input.length >= MIN_CHAR_COUNT);
        this.setState({'formLengthError': hasError});
        return hasError;
    }

    validateEmail(input) {
        const hasError = !(input === '' || (/^[^\s@]+@[^\s@]+\.[^\s@]+$/).test(input));
        this.setState({'emailError': hasError});
        return hasError;
    }

    render(props, {voteAcknowledgement}) {
        const noAnswersSubmitted = Object.keys(this.state.answers).length === 0 ||
            Object.values(this.state.answers).every((val) => val === '');
        const hasError = noAnswersSubmitted || this.state.formLengthError || this.state.emailError;
        return (
            <MainWidget
                voteAcknowledgement={voteAcknowledgement}
                onSubmit={this.onSubmit}
                onInitialSubmit={this.onInitialSubmit}
                onClear={() => this.setState({'answers': {}})}
                canShowSuggestions={props.canShowSuggestions}i
                handleOpenDrawer={props.handleOpenDrawer}
                error={hasError}>
                <FreeformQuestion
                    errorText={MIN_CHAR_ERROR_TEXT}
                    hasError={(input) => this.validateFormLength(input)}
                    store={this.makeStore('reason')}
                    placeholder="What are you trying to do?" />
                <div className="caption">{EMAIL_PROMPT_TEXT}</div>
                <InputField
                    errorText={EMAIL_ERROR_TEXT}
                    hasError={(input) => this.validateEmail(input)}
                    inputType={'email'}
                    store={this.makeStore('email')}
                    placeholder="Email address" />
                <BinaryQuestion
                    store={this.makeStore('findability')}>
                    Did you find it?</BinaryQuestion>
                <BinaryQuestion
                    store={this.makeStore('accuracy')}>
                    Was the information you found <strong>accurate</strong></BinaryQuestion>
                <BinaryQuestion
                    store={this.makeStore('clarity')}>
                    Was the information <strong>clear</strong>?</BinaryQuestion>
                <BinaryQuestion
                    store={this.makeStore('fragmentation')}>
                    Was the information you needed <strong>all on one page</strong>?
                </BinaryQuestion>
            </MainWidget>
        );
    }
}

Deluge.propTypes = {
    'project': PropTypes.string.isRequired,
    'path': PropTypes.string.isRequired,
    'canShowSuggestions': PropTypes.bool.isRequired,
    'handleOpenDrawer': PropTypes.func.isRequired
};

export default Deluge;
