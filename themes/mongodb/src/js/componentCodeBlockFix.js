/*
code-blocks with the :linenos: options render an html table, unlike
regular code-blocks. This component moves the button row into a new row
of the html table to fix the visual alignment.

https://jira.mongodb.org/browse/DOCSP-2064
*/

function isLineNumberBlock(block) {
    return Boolean(block.getElementsByClassName('linenos').length);
}

function isCaptionBlock(block) {
    return Boolean(block.getElementsByClassName('caption-text').length);
}

function hasButtonRow(block) {
    return Boolean(block.getElementsByClassName('button-row')[0]);
}

function moveButtonRowToTable(block) {
    // Select existing elements
    const buttonRow = block.getElementsByClassName('button-row')[0];
    const tableBody = block.getElementsByClassName('highlighttable')[0].childNodes[0];

    // Create new table elements
    const tableButtonRow = document.createElement('tr');
    const linenosSpacer = document.createElement('td');
    const buttonRowDestination = document.createElement('td');

    // Add class for { table-layout: fixed; } styling
    linenosSpacer.className = 'linenos-button-row-spacer';

    // Manipulate the DOM
    tableBody.prepend(tableButtonRow);
    tableButtonRow.append(linenosSpacer);
    tableButtonRow.append(buttonRowDestination);
    buttonRowDestination.append(buttonRow);
}

function moveButtonRowBelowCaption(block) {
    // Select existing elements
    const buttonRow = block.getElementsByClassName('button-row')[0];
    const caption = block.getElementsByClassName('code-block-caption')[0];

    console.log('MOVING BELOW CAPTION');

    // Manipulate the DOM
    caption.parentNode.insertBefore(buttonRow, caption.nextSibling);
}

function fixCodeBlock(block) {
    if (isLineNumberBlock(block)) {
        moveButtonRowToTable(block);
    }
    else if (isCaptionBlock(block)) {
        moveButtonRowBelowCaption(block);
    }
}

export function setup() {
    const codeblocks = document.getElementsByClassName('button-code-block');
    for (const codeblock of codeblocks) {
        if (hasButtonRow(codeblock)) {
            fixCodeBlock(codeblock);
        }
    }
}
