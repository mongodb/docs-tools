class UriwriterSingleton {
    constructor(key) {

        // an array of DOM objects that care about changes to the URI
        this.uristowrite = [];
        // this is the localCache key
        this.key = key;
        // this.uristringPasswordRedacted = 'mongodb://$[hostlist]/$[database]?$[options]';
        this.urireplacestring = '';
        this.urireplaceStringPasswordRedacted = '';
        this.templates = [];
        this.options = {};
        this.templates['self-managed MongoDB'] = {
            'options': [
                {
                    'name': 'authSource',
                    'type': 'text'
                }
            ],
            'template': 'mongodb://$[username]:$[password]@$[hostlist]/$[database]?$[options]',
            'templatePasswordRedacted': 'mongodb://$[hostlist]/$[database]?$[options]'
        };
        this.templates['replica set'] = {
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
            'templatePasswordRedacted': 'mongodb://$[hostlist]/$[database]?$[options]'
        };
        this.templates['Atlas (Cloud) with shell v. 3.6'] = {
            'options': [
                {
                    'name': 'authSource',
                    'type': 'text'
                }
            ],
            'template': 'mongodb+srv://$[username]:$[password]@$[hostlist]/$[database]?$[options]',
            'templatePasswordRedacted': 'mongodb://$[hostlist]/$[database]?$[options]'
        };
        this.templates['Atlas (Cloud) with shell v. 3.4'] = {
            'options': [
                {
                    'name': 'authSource',
                    'type': '[text]'
                },
                {
                    'name': 'ssl',
                    'type': 'pass-through',
                    'value': 'true'
                }
            ],
            'template': 'mongodb://$[username]:$[password]@$[hostlist]/$[database]?$[options]',
            'templatePasswordRedacted': 'mongodb://$[hostlist]/$[database]?$[options]'
        };
        this.setupURIListeners();
        this.renderURI();

        // this.renderOptions();
    }

    get uriwriter() {
        return JSON.parse(window.localStorage.getItem(this.key)) || {};
    }

    set uriwriter(value) {
        const uriwriter = value;
        console.log('Setting uriwriter');
        console.log(value);
        window.localStorage.setItem(this.key, JSON.stringify(uriwriter));
    }

    addValue(key, value) {
        const uriwriter = this.uriwriter;
        uriwriter[key] = value;
        this.uriwriter = uriwriter;
    }

    selectTemplate() {
        return this.templates[this.uriwriter.env];
    }

    renderURI() {
        console.log(this.uriwriter);
        console.log('******');
        if (this.uriwriter.env === undefined) {
            console.log('uriwriter env is undefined');
            const uriwriter = {};
            uriwriter.env = 'self-managed MongoDB';
            this.uriwriter = uriwriter;
        }
        const template = this.selectTemplate();
        this.uristring = template.template;
        this.uristringPasswordRedacted = template.templatePasswordRedacted;
        this.options = template.options;

        this.urireplacestring = this.replaceString(this.uristring);
        this.urireplacestringPasswordRedacted = this.replaceString(this.uristringPasswordRedacted);
        this.uristring = this.urireplacestring;
        this.uristringPasswordRedacted = this.urireplaceStringPasswordRedacted;
        this.writeToPlaceholders();
    }

    writeToPlaceholders() {
        for (let i = 0; i < this.uristowrite.length; i += 1) {
            this.uristowrite[i].innerHTML = this.uristowrite[i].innerHTML.replace(this.replaceKey, this.urireplacestring);
            this.uristowrite[i].innerHTML = this.uristowrite[i].innerHTML.replace(this.replaceKeyNoUser, this.urireplacestringPasswordRedacted);
        }
        this.replaceKey = this.urireplacestring;
        this.replaceKeyNoUser = this.urireplacestringPasswordRedacted;
    }

    setupURIListeners() {
        const list = document.getElementsByTagName('pre');
        for (let i = 0; i < list.length; i += 1) {
            if (list[i].innerHTML.indexOf('&lt;URISTRING&gt;') > -1) {
                this.uristowrite.push(list[i]);
                this.replaceKey = '&lt;URISTRING&gt;';
            }
            if (list[i].innerHTML.indexOf('&lt;URISTRING_NOUSER&gt;') > -1) {
                this.uristowrite.push(list[i]);
                this.replaceKeyNoUser = '&lt;URISTRING_NOUSER&gt;';
            }

        }
    }

    setupEnvironmentListeners() {
        const list = document.getElementsByClassName('uriwriter_sel');
        for (let i = 0; i < list.length; i += 1) {
            list[i].addEventListener('click', (event) => {
                const e = event.srcElement.innerHTML;
                this.addValue('env', e);
                // document.getElementById('uriwriter_env').innerHTML = e;
                this.renderURI();
                this.renderOptions();
                // event.preventDefault();
            });
        }
    }

    replaceString(localUriString) {

        let repl = localUriString;

        if (this.uriwriter.username) {
            repl = repl.replace('$[username]', this.uriwriter.username);
        }
        if (this.uriwriter.database) {
            repl = repl.replace('$[database]', this.uriwriter.database);
        }

        let optionsString = '';
        if (this.options.length > 0) {
            console.log('found options');
            let name = this.options[0].name;
            optionsString = `${name}=${this.getValue(this.uriwriter[name], this.options[0])}`;
        }

        for (let i = 1; i < this.options.length; i += 1) {
            let name = this.options[i].name;
            optionsString = `${optionsString},${this.options[i].name}=${this.getValue(this.uriwriter[name], this.options[i])}`;
        }

        if (optionsString.length > 0) {
            repl = repl.replace('$[options]', optionsString);
        }

        let hostport = '';

        if (this.uriwriter.hostlist && this.uriwriter.hostlist.length > 0) {
            hostport = `${this.uriwriter.hostlist[0]}`;
            for (let i = 1; i < this.uriwriter.hostlist.length; i += 1) {
                hostport += `,${this.uriwriter.hostlist[i]}`;
            }
            repl = repl.replace('$[hostlist]', hostport);
        }
        //  this.addOptions(repl);
        // if (document.getElementById('uri') !== null) {
        //    document.getElementById('uri').innerHTML = repl;
        // }
        return repl;
    }

    getValue(value, option) {
        if (option.type === 'pass-through') {
            return option.value;
        }
        return value;
    }

    renderOptions() {
        if (this.options && this.options.length > 0) {
            const optionsNode = document.getElementById('options');
            while (optionsNode.firstChild) {
                optionsNode.removeChild(optionsNode.firstChild);
            }
            for (let i = 0; i < this.options.length; i += 1) {
                if (this.options[i].type !== 'pass-through') {
                    this.renderOption(this.options[i]);
                }
            }
        }
    }

    renderOption(option) {
        const optionElement = document.createElement('fieldset');
        const inputElement = document.createElement('input');
        inputElement.setAttribute('id', option.name);
        inputElement.setAttribute('type', option.type);
        inputElement.className = 'input-uriwriter';
        if (this.uriwriter[option.name] !== undefined) {
            inputElement.value = this.uriwriter[option.name];
        }
        inputElement.addEventListener('keyup', (event) => {
            this.addValue(option.name, document.getElementById(option.name).value);
            this.renderURI();
        });
        const label = document.createElement('label');
        optionElement.appendChild(inputElement);
        label.setAttribute('for', option.name);
        label.className = 'label-uriwriter';
        label.innerHTML = option.name;
        optionElement.appendChild(label);
        document.getElementById('options').appendChild(optionElement);
    }

    setup() {
        if (document.getElementById('uriwriter') === null) {
            return;
        }
        // document.getElementById('uri').innerHTML = this.uristring;
        document.getElementById('uriwriter_act').addEventListener('click', (event) => {
            this.addHostEntryToList();
            this.renderURI();
            event.preventDefault();
        });

        document.getElementById('uriwriter_username').addEventListener('keyup', (event) => {
            this.addValue('username', document.getElementById('uriwriter_username').value);
            this.renderURI();
        });

        // document.getElementsByClassName('uriwriter_sel').addEventListener('click', (event) => {
        //    const e = event.srcElement.innerHTML;
        //    this.addValue('env', e);
        //    this.renderURI();
        //     this.renderOptions();
        // });

        document.getElementById('uriwriter_db').addEventListener('keyup', (event) => {
            this.addValue('database', document.getElementById('uriwriter_db').value);
            this.renderURI();
        });

        this.setupEnvironmentListeners();
        // this.addValue('env', 'self-managed MongoDB');
        // document.getElementById('uriwriter_env').innerHTML = 'self-managed MongoDB';
        // this.renderURI();
        this.populateForm();
    }

    populateForm() {
        this.renderOptions();
        this.renderIps();
        this.renderForm();
    }

    renderForm() {
        if (this.uriwriter.username !== null) {
            document.getElementById('uriwriter_username').value = this.uriwriter.username;
        }

        if (this.uriwriter.database !== null) {
            document.getElementById('uriwriter_db').value = this.uriwriter.database;
        }

    }

    renderIps() {
        const hostlist = this.uriwriter.hostlist;
        if (hostlist === undefined) {
            return;
        }
        for (let i = 0; i < hostlist.length; i += 1) {
            this.renderList(hostlist[i]);
        }
    }

    resetForm() {
        document.getElementById('hostname').value = '';
        document.getElementById('port').value = '';
    }


    addHostEntryToList() {

        const hostname = document.getElementById('hostname').value;
        const port = document.getElementById('port').value;

        if (hostname === '' ||
            (port === '' && this.uriwriter.env !== 'Atlas (Cloud) with shell v. 3.6')) { return; }

        this.resetForm();
        this.persistList(hostname, port);
    }

    persistList(host, port) {
        console.log('*********HOST PORT*******');
        let template = `${host}:${port}`;
        console.log(template);
        if (port === '') {
            template = `${host}`;
        }

        const uriwriter = this.uriwriter;

        if (uriwriter.hostlist) {
            const hostlist  = uriwriter.hostlist;
            if (hostlist.indexOf(template) < 0) {
                hostlist.push(template);
                uriwriter.hostlist = hostlist;
            } else {
                return;
            }
        } else {
            const array = [];
            array.push(template);
            uriwriter.hostlist = array;
        }

        this.uriwriter = uriwriter;
        this.renderList(template);
    }

    renderList(template) {
        const hostpair = document.createElement('li');
        hostpair.setAttribute('id', template);
        hostpair.setAttribute('class', 'hostpair');
        hostpair.innerHTML = template;
        const button = document.createElement('button');
        button.innerHTML = 'X';
        button.setAttribute('class', 'littlebutton');
        button.setAttribute('id', template);
        button.addEventListener('click', (event) => {
            const uriwriter = this.uriwriter;
            const localStorage = uriwriter.hostlist;
            const removeIndex = localStorage.indexOf(event.srcElement.id);
            if (removeIndex > -1) {
                localStorage.splice(removeIndex, 1);
            } else {
                return;
            }
            uriwriter.hostlist = localStorage;
            this.uriwriter = uriwriter;
            hostpair.outerHTML = '';
            this.renderURI();
        });
        hostpair.appendChild(button);
        document.getElementById('hostlist').appendChild(hostpair);
    }
}

// Create Uriwriter
export function setup() {
    (new UriwriterSingleton('uriwriter')).setup();
}
