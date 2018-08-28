import PropTypes from 'prop-types';
import preact from 'preact';

// State enum
const STATE_INITIAL = 'Initial';
const STATE_NOT_VOTED = 'NotVoted';
const STATE_VOTED = 'Voted';

class MainWidget extends preact.Component {
    constructor(props) {
        super(props);
        this.state = {
            'state': STATE_INITIAL
        };

        this.onSubmit = this.onSubmit.bind(this);
        this.onToggle = this.onToggle.bind(this);
    }

    onSubmit() {
        this.props.onSubmit(this.state.state);
        this.setState({'state': STATE_VOTED});
    }

    onToggle() {
        this.props.onClear();
        if (this.state.state === STATE_INITIAL) {
            this.setState({'state': STATE_NOT_VOTED});
        } else {
            this.setState({'state': STATE_INITIAL});
        }
    }

    render({children, voteAcknowledgement}, {state}) {
        const commentIcon = (state === STATE_INITIAL)
            ? (<span class="fa fa-comments deluge-comment-icon"></span>)
            : null;
        const closeIcon = (state !== STATE_INITIAL)
            ? (<span class="fa fa-angle-down deluge-close-icon"></span>)
            : null;
        const thankYou = (voteAcknowledgement === 'up')
            ? (<p>Thank you for your feedback!</p>)
            : null;
        const delugeBodyClass = (this.state.state === STATE_INITIAL)
            ? 'deluge-body'
            : 'deluge-body deluge-body-expanded';
        const delugeHeaderClass = (this.state.state === STATE_INITIAL)
            ? 'deluge-header'
            : 'deluge-header deluge-header-expanded';
        const delugeClass = (this.state.state === STATE_INITIAL)
            ? 'deluge'
            : 'deluge deluge-expanded';

        let body = null;
        if (voteAcknowledgement === 'down') {
            body = (
                <p>If this page contains an error, you may <a
                    class="deluge-fix-button"
                    href="https://jira.mongodb.org/">
                        report the problem on Jira.</a></p>);
        } else if (state === STATE_VOTED && !voteAcknowledgement) {
            body = (<p>Submitting feedback...</p>);
        } else if (state === STATE_NOT_VOTED) {
            body = [
                (<a key="voteup" id="rate-up"
                    onClick={() => this.setState({'state': true})}
                    class="deluge-vote-button">Yes</a>),
                (<a key="votedown" id="rate-down"
                    onClick={() => this.setState({'state': false})}
                    class="deluge-vote-button">No</a>)];
        } else if (typeof state === 'boolean') {
            const sorry = (state === false)
                ? <li>We&apos;re sorry! Please help us improve this page.</li>
                : null;

            body = (
                <div class="deluge-questions">
                    <ul>
                        {sorry}
                        {children.map((el, i) => <li key={i}>{el}</li>)}
                    </ul>

                    <div class="deluge-button-group">
                        <button onClick={this.onToggle}>Cancel</button>
                        <button class="primary"
                            onClick={this.onSubmit}>Submit</button>
                    </div>
                </div>
            );
        }


        return (
            <div class={delugeClass}>
                <div class={delugeHeaderClass} onClick={this.onToggle}>
                    {commentIcon}
                    <span class="deluge-helpful">Was this page helpful?</span>
                    {closeIcon}
                </div>

                <div class={delugeBodyClass}>
                    {thankYou}
                    {body}
                </div>
            </div>
        );
    }
}

MainWidget.propTypes = {
    'onSubmit': PropTypes.func.isRequired,
    'onClear': PropTypes.func.isRequired,
    'children': PropTypes.arrayOf(PropTypes.node),
    'voteAcknowledgement': PropTypes.string
};

export default MainWidget;
