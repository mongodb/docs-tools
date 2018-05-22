import {tabsEventDispatcher} from './componentTabs';

const LOCALSTORAGE_KEY = 'uriwriter';

const TEMPLATE_TYPE_SELF_MANAGED = 'on-premise MongoDB';
const TEMPLATE_TYPE_REPLICA_SET = 'on-premise MongoDB with replica set';
const TEMPLATE_TYPE_ATLAS_36 = 'Atlas (Cloud) v. 3.6';
const TEMPLATE_TYPE_ATLAS_34 = 'Atlas (Cloud) v. 3.4';
const TEMPLATE_TYPE_ATLAS = 'Atlas (Cloud)';

const TEMPLATES = {
    [TEMPLATE_TYPE_SELF_MANAGED]: {
        'options': [
            {
                'name': 'authSource',
                'placeholder': 'admin',
                'type': 'text'
            }
        ],
        'template': 'mongodb://$[username]:$[password]@$[hostlist]/$[database]?$[options]',
        'templatePasswordRedactedShell': 'mongodb://$[hostlist]/$[database]?$[options] --username $[username]',
        'templateShell': 'mongodb://$[username]:$[password]@$[hostlist]/$[database]?$[options]'
    },
    [TEMPLATE_TYPE_REPLICA_SET]: {
        'options': [
            {
                'name': 'replicaSet',
                'type': 'text'
            },
            {
                'name': 'authSource',
                'placeholder': 'admin',
                'type': 'text'
            },
            {
                'name': 'ssl',
                'type': 'pass-through',
                'value': 'true'
            }
        ],
        'template': 'mongodb://$[username]:$[password]@$[hostlist]/$[database]?$[options]',
        'templatePasswordRedactedShell': 'mongodb://$[hostlist]/$[database]?$[options] --username $[username] --password',
        'templateShell': 'mongodb://$[username]:$[password]@$[hostlist]/$[database]?$[options]'
    },
    [TEMPLATE_TYPE_ATLAS_36]: {
        'options': [],
        'template': 'mongodb+srv://$[username]:$[password]@$[hostlist]/$[database]?retryWrites=true',
        'templatePasswordRedactedShell': 'mongodb+srv://$[hostlist]/$[database] --username $[username] --password',
        'templateShell': 'mongodb+srv://$[username]:$[password]@$[hostlist]/$[database]'
    },
    [TEMPLATE_TYPE_ATLAS_34]: {
        'options': [
            {
                'name': 'replicaSet',
                'type': 'text'
            },
            {
                'name': 'authSource',
                'type': 'text'
            },
            {
                'name': 'ssl',
                'type': 'pass-through',
                'value': 'true'
            }
        ],
        'template': 'mongodb://$[username]:$[password]@$[hostlist]/$[database]?$[options]',
        'templatePasswordRedactedShell': 'mongodb://$[hostlist]/$[database]?replicaSet=$[replicaSet] --ssl --authenticationDatabase $[authSource] --username $[username] --password',
        'templateShell': 'mongodb://$[hostlist]/$[database]?replicaSet=$[replicaSet] --ssl --authenticationDatabase $[authSource] --username $[username] --password $[password]'
    }
};

function getValue(value, option) {
    if (option.type === 'pass-through') {
        return option.value;
    }

    return value;
}

function getPrefix(uri) {
    if ((uri.charAt(0) === '\'') ||
        (uri.charAt(0) === '"')) {
        return uri.charAt(0);
    }
    return '';
}

const PLACEHOLDER_PATTERN =
    /&lt;(?:(?:URISTRING(?:_(?:(?:SHELL_NOUSER)|(?:SHELL)))?)|(?:USERNAME))&gt;/g;
function preparseUristrings() {
    const elements = document.getElementsByTagName('pre');
    for (let i = 0; i < elements.length; i += 1) {
        elements[i].innerHTML = elements[i].innerHTML.replace(
            PLACEHOLDER_PATTERN,
            '<span class="uristring-element">$&</span>');
    }
}

function validateHost(host) {
    const parsed = (/^\s*([^:\s]+)(?::(\d+))?\s*$/).exec(host);
    if (!parsed) {
        throw new Error('Invalid host format: must match the format "hostname:port"');
    }

    const port = parseInt(parsed[2], 10);
    if (isNaN(port)) {
        throw new Error('Missing port: host must match the format "hostname:port"');
    }

    if (port > 65535) {
        throw new Error('Port number is too large');
    }

    return [parsed[1], port];
}

function conveyInvalidParse(statusElement) {
    statusElement.classList.add('mongodb-form__status--invalid');
    statusElement.classList.remove('mongodb-form__status--good');
    statusElement.style.display = '';
    statusElement.innerText = 'Connection string could not be parsed';
    // do something? email?
}

function conveyValidParse(statusElement) {
    statusElement.classList.add('mongodb-form__status--good');
    statusElement.classList.remove('mongodb-form__status--invalid');
    statusElement.style.display = '';
    statusElement.innerText = 'Connection string parsed';
}

function splitOptions(tempWriter, arrayOfMatches) {
    const settingsArray = arrayOfMatches.split('&');
    if (settingsArray.length > 0) {
        for (let i = 0; i < settingsArray.length; i += 1) {
            const keyValue = settingsArray[i].split('=');
            tempWriter[keyValue[0]] = keyValue[1];
        }
    }
}

class HostList {
    constructor(rootElement, uriWriter) {
        this.root = rootElement;

        this.uriWriter = uriWriter;
        this.elementPairs = [];
        this.updateHostsFromUriWriter();
    }

    get hosts() {
        return this.elementPairs.map((pair) => pair[0].value.trim()).filter((host) => host);
    }

    get lastInput() {
        return this.elementPairs[this.elementPairs.length - 1][0];
    }

    updateHostsFromUriWriter() {
        this.elementPairs = [];
        this.root.innerText = '';
        const state = this.uriWriter.loadState();
        for (const host of state.hostlist || []) {
            this.addHost(host);
        }

        this.addHost();
    }

    addHost(host) {
        const inputElement = document.createElement('input');
        inputElement.className = 'mongodb-form__input';
        inputElement.placeholder = 'localhost:27017';
        inputElement.value = host || '';
        const statusElement = document.createElement('div');
        statusElement.className = 'mongodb-form__status';

        inputElement.oninput = () => {
            if (inputElement.value) {
                if (this.lastInput === inputElement) {
                    this.addHost();
                }
            } else if (this.lastInput !== inputElement) {
                this.elementPairs = this.elementPairs.filter((x) => x[0] !== inputElement);
                this.root.removeChild(inputElement);
                this.root.removeChild(statusElement);

                this.uriWriter.setHosts(this.hosts);
                return;
            }

            try {
                validateHost(inputElement.value);
            } catch (err) {
                inputElement.setCustomValidity(err.message);
                statusElement.innerText = err.message;
                statusElement.classList.add('mongodb-form__status--invalid');
                return;
            }

            statusElement.innerText = '';
            statusElement.classList.remove('mongodb-form__status--invalid');
            inputElement.setCustomValidity('');

            this.uriWriter.setHosts(this.hosts);
        };

        this.root.appendChild(inputElement);
        this.root.appendChild(statusElement);
        this.elementPairs.push([inputElement, statusElement]);
    }
}

let uriwriterSingleton = null;
class UriwriterSingleton {
    constructor() {
        // an array of DOM objects that care about changes to the URI
        this.uristowrite = [];
        this.usernamestowrite = [];
        this.uristowritepasswordredactedshell = [];
        this.uristowriteshell = [];
        // this.uristringPasswordRedacted = 'mongodb://$[hostlist]/$[database]?$[options]';
        this.urireplacestring = '';
        this.options = {};

        this.hostList = null;

        // setup listeners on the page to changes in uri fields (view)
        this.setupURIListeners();
        // calculate and propagate the URI (controller)
        if (this.loadState().env === undefined) {
            this.saveState({'env': TEMPLATE_TYPE_SELF_MANAGED});
        }
        this.renderURI();
    }

    // get stuff related to this component out of local storage
    loadState() {
        return JSON.parse(window.localStorage.getItem(LOCALSTORAGE_KEY)) || {};
    }

    // put stuff related to this coponent in local storage, we only set
    // the whole thing, not portions
    saveState(state) {
        window.localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify(state));
    }

    // add or modify a value in our uriwriter in local storage.
    addValue(key, value) {
        const uriwriter = this.loadState();
        if (key !== 'atlaspasteduri' && key !== 'env') {
            delete uriwriter.atlaspasteduri;
        }
        uriwriter[key] = value;
        this.saveState(uriwriter);
    }

    // setup view hooks to change when data or environment changes
    setupURIListeners() {
        preparseUristrings();
        const list = document.getElementsByClassName('uristring-element');
        for (let i = 0; i < list.length; i += 1) {
            if (list[i].innerHTML.indexOf('&lt;URISTRING&gt;') > -1) {
                this.uristowrite.push(list[i]);
            }
            if (list[i].innerHTML.indexOf('&lt;USERNAME&gt;') > -1) {
                this.usernamestowrite.push(list[i]);
            }
            if (list[i].innerHTML.indexOf('&lt;URISTRING_SHELL&gt;') > -1) {
                this.uristowriteshell.push(list[i]);
            }
            if (list[i].innerHTML.indexOf('&lt;URISTRING_SHELL_NOUSER&gt;') > -1) {
                this.uristowritepasswordredactedshell.push(list[i]);
            }
        }
    }

    writeToPlaceholders() {
        for (let i = 0; i < this.uristowrite.length; i += 1) {
            const prefix = getPrefix(this.uristowrite[i].innerHTML);
            this.uristowrite[i].innerHTML = `${prefix}${this.urireplacestring}${prefix}`;
        }
        for (let i = 0; i < this.uristowritepasswordredactedshell.length; i += 1) {
            this.uristowritepasswordredactedshell[i].innerHTML =
                this.urireplacestringPasswordRedactedShell;
        }
        for (let i = 0; i < this.uristowriteshell.length; i += 1) {
            this.uristowriteshell[i].innerHTML = this.urireplacestringShell;
        }
        // node use case for separation of username out of uri for encoding
        for (let i = 0; i < this.usernamestowrite.length; i += 1) {
            this.usernamestowrite[i].innerHTML = this.username;
        }
    }

    setEnvironment(env) {
        const state = this.loadState();
        const isAtlas = env.startsWith(TEMPLATE_TYPE_ATLAS);
        const haveWidgetOnPage = Boolean(document.getElementById('uriwriter'));
        if (isAtlas && haveWidgetOnPage) {
            document.getElementsByClassName('atlascontrols__status')[0].style.display =
                'none';

            if (state.atlaspasteduri !== undefined) {
                // move all of this to an encapsulating function;
                this.parseIncomingAtlasString(state.atlaspasteduri);
                this.renderURI();
                this.populateForm();
                return;
            }
        }

        if (state.env.startsWith(TEMPLATE_TYPE_ATLAS) || isAtlas) {
            this.saveState({});

            if (haveWidgetOnPage) {
                this.hostList.updateHostsFromUriWriter();
            }
        }

        this.addValue('env', env);
        this.renderURI();

        if (haveWidgetOnPage) {
            this.populateForm();
        }
    }

    // this is the listener that is triggered when an environment select happens
    setupEnvironmentListeners() {
        const elements = document.getElementsByClassName('uriwriter__toggle');
        let initiallySelected = this.loadState().env;
        if (initiallySelected === TEMPLATE_TYPE_ATLAS_36 ||
            initiallySelected === TEMPLATE_TYPE_ATLAS_34) {
            initiallySelected = TEMPLATE_TYPE_ATLAS;
        }

        for (let i = 0; i < elements.length; i += 1) {
            if (initiallySelected === elements[i].innerHTML) {
                elements[i].classList.add('guide__pill--active');
            }

            elements[i].onclick = (event) => {
                const element = event.target;

                const parentChildren = element.parentElement.children;
                for (let childIndex = 0; childIndex < parentChildren.length; childIndex += 1) {
                    parentChildren[childIndex].classList.remove('guide__pill--active');
                }

                element.classList.add('guide__pill--active');
                this.setEnvironment(element.innerHTML);
            };
        }
    }

    // controller for writing the uri out to the listening html
    renderURI() {
        // User is in Atlas placeholder mode, no template defined. Can't render a uri.
        // or should we default?
        if (this.loadState().env === TEMPLATE_TYPE_ATLAS) {
            this.addValue('env', TEMPLATE_TYPE_ATLAS_36);
        }
        // we have a basic idea of the environment, get the associated uri template
        const template = TEMPLATES[this.loadState().env];

        if (!template) { return; }

        // the placeholder uri string template
        this.uristring = template.template;
        // options are environment specific settings that need to go in the uri
        this.options = template.options;
        // no we do our replacing of template fields
        this.urireplacestring = this.replaceString(this.uristring, '&');
        // on the redacted one as well
        this.urireplacestringShell = this.replaceString(template.templateShell, ',');
        this.urireplacestringPasswordRedactedShell =
            this.replaceString(template.templatePasswordRedactedShell, ',');
        this.username = this.loadState().username;
        this.writeToPlaceholders();
    }

    optionStringifier(options, optionJoinCharacter) {
        const parts = [];
        const state = this.loadState();

        for (let i = 0; i < this.options.length; i += 1) {
            const option = this.options[i];
            const name = option.name;
            let value = getValue(state[name], option);
            if (!value) {
                if (option.placeholder) {
                    value = option.placeholder;
                } else {
                    value = `$[${name}]`;
                }
            }
            parts.push(`${name}=${value}`);
        }

        return parts.join(optionJoinCharacter);
    }

    replaceString(localUriString, optionJoinCharacter) {
        const state = this.loadState();

        // replace hardcoded plaments (why oh why do we do this????)
        if (state.username) {
            localUriString = localUriString.replace('$[username]', state.username);
        }
        if (state.database) {
            localUriString = localUriString.replace('$[database]', state.database);
        }
        if (state.authSource) {
            localUriString = localUriString.replace('$[authSource]', state.authSource);
        }
        if (state.replicaSet) {
            localUriString = localUriString.replace('$[replicaSet]', state.replicaSet);
        }

        // replace options where they exist
        const optionsString = this.optionStringifier(this.options, optionJoinCharacter);

        if (optionsString.length > 0) {
            localUriString = localUriString.replace('$[options]', optionsString);
        }

        // get our hosts and ports in
        if (state.hostlist && state.hostlist.length > 0) {
            localUriString = localUriString.replace('$[hostlist]', state.hostlist.join(','));
        }

        return localUriString;
    }

    renderOptions() {
        const elements = document.getElementsByClassName('uriwriter__option-prompt');
        while (elements.length > 0) {
            elements[0].parentElement.removeChild(elements[0]);
        }

        if (this.options && this.options.length > 0) {
            for (let i = 0; i < this.options.length; i += 1) {
                if (this.options[i].type !== 'pass-through') {
                    this.renderOption(this.options[i]);
                }
            }
        }
    }

    renderOption(option) {
        const optionElement = document.createElement('label');
        optionElement.className = 'mongodb-form__prompt uriwriter__option-prompt';

        const label = document.createElement('div');
        label.className = 'mongodb-form__label';
        label.innerText = option.name;

        const inputElement = document.createElement('input');
        inputElement.setAttribute('id', option.name);
        if (option.placeholder) {
            inputElement.setAttribute('placeholder', option.placeholder);
        }
        inputElement.className = 'mongodb-form__input';
        if (this.loadState()[option.name] !== undefined) {
            inputElement.value = this.loadState()[option.name];
        }
        inputElement.addEventListener('input', (event) => {
            this.addValue(option.name, document.getElementById(option.name).value);
            this.renderURI();
        });

        optionElement.appendChild(label);
        optionElement.appendChild(inputElement);

        const serverPromptElement = document.querySelector('[data-server-configuration]');
        serverPromptElement.parentElement.insertBefore(optionElement, serverPromptElement);
    }

    initializeWidget() {
        if (!document.getElementById('uriwriter')) {
            return;
        }

        this.hostList = new HostList(document.getElementById('hostlist'), this);

        document.getElementById('uriwriter_username').addEventListener('input', (event) => {
            this.addValue('username', event.target.value);
            this.renderURI();
        });

        const atlaspaste = document.getElementById('uriwriter_atlaspaste');
        const statusElement = document.getElementsByClassName('atlascontrols__status')[0];

        atlaspaste.oninput = (event) => {
            const pastedValue = atlaspaste.value;
            if (!pastedValue.trim()) {
                statusElement.style.display = 'none';
                atlaspaste.setCustomValidity('');
                return;
            }

            if (!this.parseIncomingAtlasString(pastedValue)) {
                atlaspaste.setCustomValidity('Failed to parse');
                conveyInvalidParse(statusElement);
            } else {
                atlaspaste.setCustomValidity('');
                this.addValue('atlaspasteduri', pastedValue);
                conveyValidParse(statusElement);
                this.renderURI();
                this.populateForm();
            }
        };

        document.getElementById('uriwriter_db').addEventListener('input', (event) => {
            this.addValue('database', document.getElementById('uriwriter_db').value);
            this.renderURI();
        });

        this.setupEnvironmentListeners();
        this.populateForm();
    }

    renderFormValues() {
        const state = this.loadState();
        const atlasControlsElement = document.getElementsByClassName('uriwriter__atlascontrols')[0];
        if (state.env === TEMPLATE_TYPE_SELF_MANAGED || state.env === TEMPLATE_TYPE_REPLICA_SET) {
            atlasControlsElement.style.display = 'none';
            document.getElementById('userinfo_form').style.display = '';
        } else {
            document.getElementById('uriwriter_atlaspaste').value = state.atlaspasteduri || '';

            if (state.atlaspasteduri !== undefined) {
                atlasControlsElement.style.display = '';
            } else {
                atlasControlsElement.style.display = 'none';
            }

            document.getElementById('userinfo_form').style.display = 'none';
            atlasControlsElement.style.display = '';
            return;
        }
        if (state.username !== undefined) {
            document.getElementById('uriwriter_username').value = state.username;
        }
        if (state.database !== undefined) {
            document.getElementById('uriwriter_db').value = state.database;
        }
    }

    /** IP related functions **/

    setHosts(hostlist) {
        const uriwriter = this.loadState();
        uriwriter.hostlist = hostlist;
        this.saveState(uriwriter);
        this.renderURI();
    }

    populateForm() {
        this.renderOptions();
        this.renderFormValues();
    }


    /** Atlas copy paste parse and processing **/

    parseOutShellParams(splitOnSpace, tempWriter) {
        // go through all of the command line args, parse
        for (let i = 0; i < splitOnSpace.length; i += 1) {
            if (splitOnSpace[i].startsWith('--')) {
                // this is a key, if next val does not begin with --, its a value
                if (!splitOnSpace[i + 1].startsWith('--')) {
                    let splitKey = splitOnSpace[i].replace('--', '');
                    let splitValue = splitOnSpace[i + 1];

                    if (splitKey === 'authenticationDatabase') {
                        splitKey = 'authSource';
                    }

                    // sometimes the next string is another parameter,
                    // ignore those as they are canned
                    if (!splitValue.startsWith('--')) {
                        // get rid of brackets which can cause problems with our inline code
                        splitValue = splitValue.replace('<', '').replace('>', '');
                        tempWriter[splitKey] = splitValue;
                    }
                }
            }
        }
    }

    parseOutURIParams(shellString, tempWriter) {
        const uriParamArray = shellString.split('&');
        for (let i = 0; i < uriParamArray.length; i += 1) {
            const keyValueString = uriParamArray[i];
            const keyValueArray = keyValueString.split('=');
            tempWriter[keyValueArray[0]] = keyValueArray[1];
        }
    }

    parseOutEnvAndClusters(splitOnSpaceClusterEnv, tempWriter) {
        // depending on whether this is 3.6 or 3.4 the cluster info looks slightly different
        // 3.4 uses the URI to pass in a replica set name
        let shellMatch = /(\w+):\/\/((\S+)(:)+(\S+))\/(\w+)?\?(\S+)/;
        const shellMatch36 = /((\w+)\+(\w+)):\/\/((\S+))\/(\w+)/;
        if (splitOnSpaceClusterEnv.startsWith('mongodb+srv')) {
            shellMatch = shellMatch36;
        }
        const shellArray = splitOnSpaceClusterEnv.match(shellMatch);
        // add length check here?
        if (shellArray[1] === 'mongodb') {
            tempWriter.env = TEMPLATE_TYPE_ATLAS_34;
            const hostListString = shellArray[2];
            tempWriter.hostlist = hostListString.split(',');
            this.parseOutURIParams(shellArray[7], tempWriter);
        } else {
            tempWriter.env = TEMPLATE_TYPE_ATLAS_36;
            tempWriter.hostlist = [shellArray[4]];
        }
        tempWriter.database = shellArray[6];
    }
    // mongo "mongodb://cluster0-shard-00-00-igkvv.mongodb.net:27017,cluster0-shard-00-01-igkvv.mongodb.net:27017,cluster0-shard-00-02-igkvv.mongodb.net:27017/test?replicaSet=Cluster0-shard-0" --ssl --authenticationDatabase admin --username mongodb-stitch-easy_bake_oven-aluyj --password <PASSWORD>
    // mongo "mongodb+srv://cluster0-igkvv.mongodb.net/test" --username mongodb-stitch-easy_bake_oven-aluyj
    parseShell(atlasString, tempWriter) {
        // split out the mongo and parse the rest
        const splitOnSpace = atlasString.split(' ');
        let splitOnSpaceClusterEnv = splitOnSpace[1];
        // get rid of double quotes
        splitOnSpaceClusterEnv = splitOnSpaceClusterEnv.replace(/"/g, '');
        // get command line args
        this.parseOutShellParams(splitOnSpace, tempWriter);
        // get the cluster information
        this.parseOutEnvAndClusters(splitOnSpaceClusterEnv, tempWriter);

        this.saveState(tempWriter);

        // we need to define success
        return true;
    }

    // get the pasted string and parse it out
    parseIncomingAtlasString(pastedValue) {
        if (pastedValue === undefined) {
            return false;
        }
        // trim any carriage return line feed business
        pastedValue = pastedValue.replace(/[\n\r]+/g, '').trim();
        if (pastedValue !== null) {
            const status = this.parseAtlasString(pastedValue);
            this.hostList.updateHostsFromUriWriter();
            return status;
        }
        return false;
    }

    // this is a 3.4 URI
    // mongodb://<USERNAME>:<PASSWORD>@cluster0-shard-00-00-juau5.mongodb.net:27017,cluster0-shard-00-01-juau5.mongodb.net:27017,cluster0-shard-00-02-juau5.mongodb.net:27017/test?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin
    parseTo3dot4(atlasString, tempWriter) {
        tempWriter.env = TEMPLATE_TYPE_ATLAS_34;
        // save the environment selection
        this.saveState(tempWriter);
        tempWriter = this.loadState();
        const re = /(\S+):\/\/(\S+):(\S*)@(\S+)\/(\S+)\?(\S+)/;
        const matchesArray = atlasString.match(re);
        if (!matchesArray) {
            return false;
        }

        tempWriter.username = matchesArray[2];
        tempWriter.hostlist = matchesArray[4].split(',');
        tempWriter.database = matchesArray[5];
        splitOptions(tempWriter, matchesArray[6]);
        this.saveState(tempWriter);
        return true;
    }

    // this is a 3.6 url, parse accordingly
    // ex: mongodb+srv://<USERNAME>:<PASSWORD>@cluster0-juau5.mongodb.net/test
    parseTo3dot6(atlasString, tempWriter) {
        tempWriter.env = TEMPLATE_TYPE_ATLAS_36;
        // save the environment selection
        this.saveState(tempWriter);
        tempWriter = this.loadState();
        // regexp for 3.6 format
        const re = /(\S+):\/\/(\S+):(\S*)@(\S+)\/([^\s?]+)\?/;
        const matchesArray = atlasString.match(re);
        if (!matchesArray) {
            return false;
        }

        tempWriter.username = matchesArray[2];
        tempWriter.havePassword = Boolean(matchesArray[3]);
        tempWriter.hostlist = [matchesArray[4]];
        tempWriter.database = matchesArray[5];
        this.saveState(tempWriter);
        return true;
    }

    parseAtlasString(atlasString) {
        const tempWriter = this.loadState();
        // add shell parser here
        if (atlasString.indexOf(' --') > -1) {
            return this.parseShell(atlasString, tempWriter);
        }
        if (atlasString.startsWith('mongodb+srv')) {
            return this.parseTo3dot6(atlasString, tempWriter);
        }
        return this.parseTo3dot4(atlasString, tempWriter);
    }
}

tabsEventDispatcher.listen((ctx) => {
    if (!uriwriterSingleton) { return; }
    if (ctx.tabId === 'atlascloud') {
        uriwriterSingleton.setEnvironment(TEMPLATE_TYPE_ATLAS);
    }
});

// Create Uriwriter
export function setup() {
    uriwriterSingleton = new UriwriterSingleton();
    uriwriterSingleton.initializeWidget();
}
