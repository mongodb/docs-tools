/*
code-blocks with the :linenos: options render an html table, unlike
regular code-blocks. This component moves the button row into a new row
of the html table to fix the visual alignment.

https://jira.mongodb.org/browse/DOCSP-2064
*/

function isLineNumberBlock(block) {
    return Boolean(block.getElementsByClassName('linenos').length);
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

function fixCodeBlock(block) {
    if (hasButtonRow(block) && isLineNumberBlock(block)) {
        moveButtonRowToTable(block);
    }
}

export function setup() {
    const codeblocks = document.getElementsByClassName('button-code-block');
    for (const codeblock of codeblocks) {
        fixCodeBlock(codeblock);
    }
}
