import {AnonymousCredential, Stitch} from 'mongodb-stitch-browser-sdk';
import FreeformQuestion from './FreeformQuestion';
import InputField from './InputField';
import MainWidget from './MainWidget';
import PropTypes from 'prop-types';
import preact from 'preact';

const MIN_CHAR_COUNT = 15;
const MIN_CHAR_ERROR_TEXT = `Please respond with at least ${MIN_CHAR_COUNT} characters.`;
const EMAIL_ERROR_TEXT = 'Please enter a valid email address.';
const EMAIL_PROMPT_TEXT = 'May we contact you about your feedback?';

class Deluge extends preact.Component {
    constructor(props) {
        super(props);
        this.state = {
            'answers': {},
            'emailError': false,
            'formLengthError': false,
            'voteAcknowledgement': null,
            'voteId': undefined
        };
        this.onSubmitFeedback = this.onSubmitFeedback.bind(this);
        this.onSubmitVote = this.onSubmitVote.bind(this);
    }

    componentDidMount() {
        this.setupStitch();
    }

    setupStitch() {
        const appName = null;
        this.stitchClient = Stitch.hasAppClient(appName)
            ? Stitch.defaultAppClient
            : Stitch.initializeDefaultAppClient(appName);
        this.stitchClient.auth.loginWithCredential(new AnonymousCredential()).catch((err) => {
            console.error(err);
        });
    }

    onSubmitVote(vote) {
        this.sendVote(vote).then((result) => {
            this.setState({
                'voteAcknowledgement': (vote) ? 'up' : 'down',
                'voteId': result.insertedId
            });
        }).
            catch((err) => {
                console.error(err);
            });
    }

    sendVote(vote) {
        const path = `${this.props.project}/${this.props.path}`;

        // Report to Segment
        const analyticsData = {
            'useful': vote
        };

        try {
            const user = window.analytics.user();
            const segmentUID = user.id();
            if (segmentUID) {
                analyticsData.segmentUID = segmentUID.toString();
            } else {
                analyticsData.segmentAnonymousID = user.anonymousId().toString();
            }
            window.analytics.track('Vote Submitted', analyticsData);
        } catch (err) {
            console.error(err);
        }

        const voteDocument = {
            'useful': vote,
            'page': path,
            'url': location.href,
            'date': new Date()
        };

        return this.stitchClient.callFunction('submitVote', [voteDocument]);
    }

    onSubmitFeedback(vote) {
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

        this.sendFeedback(vote, fields).catch((err) => {
            console.error(err);
        });
    }

    sendFeedback(vote, fields) {
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

        if (!this.state.voteId) {
            return Promise.reject(new Error('Could not locate document ID'));
        }

        const query = {'_id': this.state.voteId};
        const update = {
            '$set': {
                ...fields
            }
        };

        return this.stitchClient.callFunction('submitFeedback', [query, update]);
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
                onSubmitFeedback={this.onSubmitFeedback}
                onSubmitVote={this.onSubmitVote}
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
