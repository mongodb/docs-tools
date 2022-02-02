import Menu from './menu.js';
import Submenu from './submenu.js';
import classNames from 'classnames';
import preact from 'preact';

class NavbarDropdown extends preact.Component {
    constructor(props) {
        super(props);
        this.state = {
            'open': false
        };

        this.toggle = this.toggle.bind(this);
    }

    toggle(event) {
        this.setState({
            'open': !this.state.open
        });
    }

    render({baseUrl}) {
        const dropDownClass = classNames({
            'navbar-dropdown': true,
            'navbar-dropdown--open': this.state.open
        });

        const menuClass = classNames({
            'navbar-dropdown__menu': true,
            'navbar-dropdown__menu--hidden': !this.state.open,
            'navbar-dropdown__menu--shown': this.state.open
        });

        let baseUrls = {
            'base': 'https://docs.mongodb.com',
            'atlas': 'https://docs.atlas.mongodb.com',
            'opsmanager': 'https://docs.opsmanager.mongodb.com',
            'cloudmanager': 'https://docs.cloudmanager.mongodb.com'
        };

        if (baseUrl === 'https://www.mongodb.com/docs') {
            baseUrls = {
                'base': `${baseUrl}`,
                'atlas': `${baseUrl}/atlas`,
                'opsmanager': `${baseUrl}/opsmanager`,
                'cloudmanager': `${baseUrl}/cloudmanager`
            };
        }

        return (
            <div className={ dropDownClass }>
                <span className="navbar-dropdown__label" onClick={this.toggle}>Documentation</span>

                <div className={ menuClass }>
                    <Menu>
                        <li className="menu__item">
                            <a href={`${baseUrls.base}/`}>Docs Home</a>
                        </li>
                        <li className="menu__item">
                            <Submenu title="Documentation" open={true}>
                                <li className="submenu__item">
                                    <a href={`${baseUrls.base}/manual/`}>MongoDB Server</a>
                                </li>
                                <li className="submenu__item">
                                    <Submenu title="Drivers" open={false}>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/drivers/c/`}>C</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/drivers/cxx/`}>C++</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/drivers/csharp/`}>C#</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/drivers/java-drivers/`}>Java</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/drivers/node/`}>Node.js</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/drivers/perl/`}>Perl</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/drivers/php/`}>PHP</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/drivers/python/`}>Python</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/drivers/ruby/`}>Ruby</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/drivers/scala/`}>Scala</a>
                                        </li>
                                    </Submenu>
                                </li>

                                <li className="submenu__item submenu__item--nested">
                                    <Submenu title="Cloud" open={true}>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.atlas}/`}>MongoDB Atlas</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/datalake/`}>MongoDB Atlas Data Lake</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.atlas}/atlas-search/`}>MongoDB Atlas Search</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.cloudmanager}/`}>MongoDB Cloud Manager</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.opsmanager}/current/`}>MongoDB Ops Manager</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/realm/`}>MongoDB Realm</a>
                                        </li>
                                    </Submenu>
                                </li>

                                <li className="submenu__item submenu__item--nested">
                                    <Submenu title="Tools" open={true}>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/atlas-open-service-broker/current/`}>MongoDB Atlas Open Service Broker</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/bi-connector/current/`}>MongoDB BI Connector</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/charts/saas/`}>MongoDB Charts</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/mongocli/stable/`}>MongoDB Command Line Interface</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://github.com/mongodb/mongodb-kubernetes-operator">MongoDB Community Kubernetes Operator</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/compass/current/`}>MongoDB Compass</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/database-tools/`}>MongoDB Database Tools</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/kubernetes-operator/stable/`}>MongoDB Enterprise Kubernetes Operator</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/kafka-connector/current/`}>MongoDB Kafka Connector</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/mongodb-shell/`}>MongoDB Shell</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/spark-connector/current/`}>MongoDB Spark Connector</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href={`${baseUrls.base}/mongodb-vscode/`}>MongoDB for VS Code</a>
                                        </li>
                                    </Submenu>
                                </li>

                                <li className="submenu__item">
                                    <a href={`${baseUrls.base}/guides/`}>Guides</a>
                                </li>
                            </Submenu>
                        </li>
                        <li className="menu__item menu__item--secondary">
                            <a href="https://www.mongodb.com/">Company</a>
                        </li>
                        <li className="menu__item menu__item--secondary">
                            <a href="https://university.mongodb.com/">Learn</a>
                        </li>
                        <li className="menu__item menu__item--secondary">
                            <a href="https://www.mongodb.com/community">Community</a>
                        </li>
                        <li className="menu__item menu__item--secondary">
                            <a href="https://www.mongodb.com/what-is-mongodb">What is MongoDB</a>
                        </li>
                        <li className="menu__item menu__item--secondary">
                            <a href="https://www.mongodb.com/download-center?tck=docs">Get MongoDB</a>
                        </li>
                        <li className="menu__item menu__item--secondary">
                            <a href="https://www.mongodb.com/contact?tck=docs">Contact Us</a>
                        </li>
                    </Menu>
                </div>
            </div>
        );
    }
}

export default NavbarDropdown;
