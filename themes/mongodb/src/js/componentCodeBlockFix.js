function isLineNumberBlock(block) {
    return Boolean(block.getElementsByClassName('linenos').length);
}

function hasButtonRow(block) {
    return Boolean(block.getElementsByClassName('button-row')[0]);
}

function hasAtLeastOneButton(block) {
    return Boolean(block.getElementsByClassName('button-row')[0].children.length);
}

function getButtonRow(block) {
    return hasButtonRow(block)
        ? block.getElementsByClassName('button-row')[0]
        : null;
}

function moveButtonRowToTable(block) {
    const br = getButtonRow(block);
    const tdLinenos = document.createElement('td');
    tdLinenos.id = 'linenos-button-row-filler';
    const tdCode = document.createElement('td');
    tdCode.append(br);
    console.log('brbrbr', tdCode);
    const tr = document.createElement('tr');
    tr.append(tdLinenos);
    tr.append(tdCode);

    block.getElementsByClassName('highlighttable')[0].childNodes[0].prepend(tr);
}

function doIt(block) {
    if (hasButtonRow(block) && isLineNumberBlock(block)) {
        moveButtonRowToTable(block);
    }
}

export function setup() {
    const codeblocks = document.getElementsByClassName('button-code-block');
    for (const codeblock of codeblocks) {
        doIt(codeblock);
    }
}
