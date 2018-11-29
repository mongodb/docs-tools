import PropTypes from 'prop-types';
import preact from 'preact';

function addQueryParameters(url, pageName) {
    return `${url}?suggestor=${encodeURIComponent(pageName)}`;
}

function SuggestionCard({suggestion}) {
    const urlWithParams = addQueryParameters(suggestion.url, this.props.pageName);
    return (
        <div className="suggestion-card">
            <a href={urlWithParams}>
                <div>
                    <h2>{suggestion.title}</h2>
                    {suggestion.description && <p>{suggestion.description}</p>}
                </div>
            </a>
        </div>
    );
}

function EmptyCard({handleDismissCard}) {
    return (
        <div className="suggestion-card suggestion-close"
            onClick={() => handleDismissCard()}>
            <h2>This isn&#39;t what I was looking for</h2>
        </div>
    );
}

class SuggestionCardList extends preact.Component {
    render() {
        const suggestions = this.props.suggestions;
        const suggestionCards = suggestions.map((suggestion) =>
            <SuggestionCard
                suggestion={suggestion}
                key={suggestion.url}
                pageName={this.props.pageName}
            />
        );
        return (
            <div>
                {suggestionCards}
                <EmptyCard handleDismissCard={this.props.handleDismissCard} />
            </div>
        );
    }
}

SuggestionCard.propTypes = {
    'pageName': PropTypes.string.isRequired,
    'suggestion': PropTypes.object.isRequired
};

EmptyCard.propTypes = {
    'handleDismissCard': PropTypes.func.isRequired
};

SuggestionCardList.propTypes = {
    'suggestions': PropTypes.array.isRequired,
    'handleDismissCard': PropTypes.func.isRequired,
    'pageName': PropTypes.string.isRequired
};

export default SuggestionCardList;
