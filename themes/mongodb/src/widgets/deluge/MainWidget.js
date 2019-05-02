import PropTypes from 'prop-types';
import preact from 'preact';

// State enum
const STATE_INITIAL = 'Initial';
const STATE_VOTED = 'Voted';

class MainWidget extends preact.Component {
    constructor(props) {
        super(props);
        this.state = {
            'state': STATE_INITIAL
        };

        this.onSubmitFeedback = this.onSubmitFeedback.bind(this);
        this.onInitialVote = this.onInitialVote.bind(this);
        this.onToggle = this.onToggle.bind(this);
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

    onToggle() {
        this.props.onClear();
        if (this.state.state === STATE_INITIAL) {
            return;
        }
        this.setState({'state': STATE_INITIAL});
    }

    render({children, canShowSuggestions, voteAcknowledgement}, {state}) {
        const delugeBodyClass = (state === STATE_INITIAL)
            ? 'deluge-body'
            : 'deluge-body deluge-body-expanded';
        const delugeHeaderClass = (state === STATE_INITIAL)
            ? 'deluge-header'
            : 'deluge-header deluge-header-expanded';
        const delugeClass = (state === STATE_INITIAL)
            ? 'deluge'
            : 'deluge deluge-expanded';

        let body = null;
        if (state === STATE_VOTED && voteAcknowledgement === 'down') {
            body = (
                <p>If this page contains an error, you may <a
                    class="deluge-fix-button"
                    href="https://jira.mongodb.org/">
                        report the problem on Jira.</a></p>);
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
                            <button onClick={this.onToggle}>Cancel</button>
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
                            <button onClick={this.onToggle}>Cancel</button>
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
                <div class={delugeHeaderClass} onClick={this.onToggle}>
                    {state === STATE_INITIAL &&
                        <span class="fa fa-comments deluge-comment-icon"></span>}
                    <span class="deluge-helpful">Was this page helpful?</span>
                    {state !== STATE_INITIAL &&
                        <span class="fa fa-angle-down deluge-close-icon"></span>}
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
                    {state === STATE_VOTED &&
                        voteAcknowledgement === 'up' &&
                        <p>Thank you for your feedback!</p>}
                    {body}
                </div>
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
