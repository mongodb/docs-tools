import BinaryQuestion from './BinaryQuestion';
import FreeformQuestion from './FreeformQuestion';
import MainWidget from './MainWidget';
import PropTypes from 'prop-types';
import preact from 'preact';

const FEEDBACK_URL = 'http://deluge.us-east-1.elasticbeanstalk.com/';

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
            'voteAcknowledgement': null
        };
        this.onSubmit = this.onSubmit.bind(this);
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

        this.sendRating(vote, fields).then(() => {
            this.setState({
                'voteAcknowledgement': (vote) ? 'up' : 'down'
            });
        }).
            catch((err) => {
                console.error(err);
            });
    }

    sendRating(vote, fields) {
        const path = `${this.props.project}/${this.props.path}`;

        // Report to Segment
        const analyticsData = {
            'useful': vote,
            ...fields
        };

        try {
            fields.segmentUID = window.analytics.user().
                id().
                toString();
            window.analytics.track('Feedback Submitted', analyticsData);
        } catch (err) {
            console.error(err);
        }

        // Report to Deluge
        return new Promise((resolve, reject) => {
            const url = addQueryParameters(FEEDBACK_URL, {
                ...fields,
                'v': vote,
                'p': path,
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

    render(props, {voteAcknowledgement}) {
        return (
            <MainWidget
                voteAcknowledgement={voteAcknowledgement}
                onSubmit={this.onSubmit}
                onClear={() => this.setState({'answers': {}})}>
                <FreeformQuestion
                    store={this.makeStore('reason')}
                    placeholder="What were you looking for?" />
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
    'path': PropTypes.string.isRequired
};

export default function deluge(project, path, rootElement) {
    preact.render('', rootElement, rootElement._delugeRendered);

    if (path) {
        rootElement._delugeRendered = preact.render(
            <Deluge project={project} path={path} />,
            rootElement);
    }
}
