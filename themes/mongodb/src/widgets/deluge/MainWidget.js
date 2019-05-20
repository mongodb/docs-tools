import PropTypes from 'prop-types';
import preact from 'preact';

// State enum
const STATE_INITIAL = 'Initial';
const STATE_VOTED = 'Voted';

class MainWidget extends preact.Component {
    constructor(props) {
        super(props);
        this.state = {
            'closed': false,
            'state': STATE_INITIAL
        };

        this.onSubmitFeedback = this.onSubmitFeedback.bind(this);
        this.onInitialVote = this.onInitialVote.bind(this);
        this.toggleVisibility = this.toggleVisibility.bind(this);
    }

    componentDidMount() {
        const savedFeedbackState = JSON.parse(window.sessionStorage.getItem('feedbackHidden'));
        if (savedFeedbackState) {
            this.setState({'closed': savedFeedbackState});
        }
    }

    onSubmitFeedback() {
        this.props.onSubmitFeedback(this.state.state);
        this.setState({'state': STATE_VOTED});
    }

    onInitialVote(e, state) {
        e.stopPropagation();
        this.setState({'state': state});
        this.props.onSubmitVote(state);
        if (state === false) {
            this.props.handleOpenDrawer();
        }
    }

    toggleVisibility(event) {
        const {closed, state} = this.state;
        event.stopPropagation();
        if ((typeof state === 'boolean' || state === STATE_VOTED) && closed === false) {
            this.setState({'state': STATE_INITIAL});
        }
        this.setState(
            (prevState) => ({'closed': !prevState.closed}),
            () => window.sessionStorage.setItem('feedbackHidden', JSON.stringify(this.state.closed))
        );
    }

    render({children, canShowSuggestions, voteAcknowledgement}, {closed, state}) {
        const delugeBodyClass = (state === STATE_INITIAL)
            ? 'deluge-body'
            : 'deluge-body deluge-body-expanded';
        const delugeHeaderClass = 'deluge-header';
        const delugeClass = (state !== STATE_INITIAL && closed === false)
            ? 'deluge deluge-expanded'
            : 'deluge';

        let body = null;
        if (state === STATE_VOTED) {
            body = (
                <div>
                    <p>Thank you for your feedback!</p>
                    <p>If this page contains an error, you may <a
                        class="deluge-fix-button"
                        href="https://jira.mongodb.org/">
                            report the problem on Jira.</a></p>
                    <p>We also recommend you explore <a class="deluge-fix-button"
                        href="https://groups.google.com/group/mongodb-user">
                            the MongoDB discussion forum</a> for additional support.</p>
                    <p className="deluge-close-link"><small><span onClick={this.toggleVisibility}>
                        Close</span></small></p>
                </div>);
        } else if (state === STATE_VOTED && !voteAcknowledgement) {
            body = (<p>Submitting feedback...</p>);
        } else if (typeof state === 'boolean') {
            const sorry = (state === false)
                ? <li>We&apos;re sorry! Please help us improve this page.</li>
                : null;

            if (canShowSuggestions) {
                const commentBox = children[0];
                body = (
                    <div class="deluge-questions">
                        <ul>
                            {sorry}
                            <li>{commentBox}</li>
                        </ul>

                        <div class="deluge-button-group">
                            <button onClick={this.toggleVisibility}>Cancel</button>
                            <button class="primary"
                                onClick={this.onSubmitFeedback}
                                disabled={this.props.error}>Submit</button>
                        </div>
                    </div>
                );
            } else {
                body = (
                    <div class="deluge-questions">
                        <ul>
                            {sorry}
                            {children.map((el, i) => <li key={i}>{el}</li>)}
                        </ul>

                        <div class="deluge-button-group">
                            <button onClick={this.toggleVisibility}>Cancel</button>
                            <button class="primary"
                                onClick={this.onSubmitFeedback}
                                disabled={this.props.error}>Submit</button>
                        </div>
                    </div>
                );
            }
        }


        return (
            <div class={delugeClass}>
                {closed ? (
                    <div class="deluge-header deluge-header-minimized"
                        onClick={this.toggleVisibility}>
                        <span class="fa fa-angle-up deluge-open-icon"></span>
                    </div>
                ) : (
                    <div>
                        <div class={delugeHeaderClass}>
                            <span class="fa fa-angle-down deluge-close-icon-hidden"></span>
                            <span class="deluge-helpful">Was this page helpful?</span>
                            <span class="fa fa-angle-down deluge-close-icon"
                                onClick={this.toggleVisibility}></span>
                        </div>
                        {state === STATE_INITIAL && (
                            <div class="deluge-vote">
                                <a key="voteup" id="rate-up"
                                    onClick={(e) => this.onInitialVote(e, true)}>Yes</a>
                                <a key="votedown" id="rate-down"
                                    onClick={(e) => this.onInitialVote(e, false)}>No</a>
                            </div>
                        )}

                        <div class={delugeBodyClass}>
                            {body}
                        </div>
                    </div>
                )}
            </div>
        );
    }
}

MainWidget.propTypes = {
    'error': PropTypes.bool.isRequired,
    'onSubmitFeedback': PropTypes.func.isRequired,
    'onSubmitVote': PropTypes.func.isRequired,
    'onClear': PropTypes.func.isRequired,
    'children': PropTypes.arrayOf(PropTypes.node),
    'voteAcknowledgement': PropTypes.string,
    'handleOpenDrawer': PropTypes.func.isRequired,
    'canShowSuggestions': PropTypes.bool.isRequired
};

export default MainWidget;
