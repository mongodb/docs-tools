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

    render() {
        const dropDownClass = classNames({
            'navbar-dropdown': true,
            'navbar-dropdown--open': this.state.open
        });

        const menuClass = classNames({
            'navbar-dropdown__menu': true,
            'navbar-dropdown__menu--hidden': !this.state.open,
            'navbar-dropdown__menu--shown': this.state.open
        });

        return (
            <div className={ dropDownClass }>
                <span className="navbar-dropdown__label" onClick={this.toggle}>Documentation</span>

                <div className={ menuClass }>
                    <Menu>
                        <li className="menu__item">
                            <a href="https://docs.mongodb.com/">Docs Home</a>
                        </li>
                        <li className="menu__item">
                            <Submenu title="Documentation" open={true}>
                                <li className="submenu__item">
                                    <a href="https://docs.mongodb.com/manual/">MongoDB Server</a>
                                </li>
                                <li className="submenu__item">
                                    <Submenu title="Drivers" open={false}>
                                        <li className="submenu__item">
                                            <a href="http://mongoc.org/libmongoc/current/">C</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://mongodb.github.io/mongo-cxx-driver/">C++11</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/ecosystem/drivers/csharp/">C#</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="http://mongodb.github.io/mongo-java-driver/">Java</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://mongodb.github.io/node-mongodb-native/">Node.js</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/ecosystem/drivers/perl/">Perl</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/ecosystem/drivers/php/">PHP</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/ecosystem/drivers/python/">Python</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/ecosystem/drivers/ruby/">Ruby</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/ecosystem/drivers/scala/">Scala</a>
                                        </li>
                                    </Submenu>
                                </li>

                                <li className="submenu__item submenu__item--nested">
                                    <Submenu title="Cloud" open={true}>
                                        <li className="submenu__item">
                                            <a href="https://docs.atlas.mongodb.com/">MongoDB Atlas</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/datalake/">MongoDB Atlas Data Lake</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.atlas.mongodb.com/atlas-search/">MongoDB Atlas Search</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.cloudmanager.mongodb.com/">MongoDB Cloud Manager</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.opsmanager.mongodb.com/current/">MongoDB Ops Manager</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/realm/">MongoDB Realm</a>
                                        </li>
                                    </Submenu>
                                </li>

                                <li className="submenu__item submenu__item--nested">
                                    <Submenu title="Tools" open={true}>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/atlas-open-service-broker/current/">MongoDB Atlas Open Service Broker</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/bi-connector/current/">MongoDB BI Connector</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/charts/saas/">MongoDB Charts</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/mongocli/stable/">MongoDB Command Line Interface</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://github.com/mongodb/mongodb-kubernetes-operator">MongoDB Community Kubernetes Operator</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/compass/current/">MongoDB Compass</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/database-tools/">MongoDB Database Tools</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/kubernetes-operator/stable/">MongoDB Enterprise Kubernetes Operator</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/kafka-connector/current/">MongoDB Kafka Connector</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/mongodb-shell/">MongoDB Shell</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/spark-connector/current/">MongoDB Spark Connector</a>
                                        </li>
                                        <li className="submenu__item">
                                            <a href="https://docs.mongodb.com/mongodb-vscode/">MongoDB for VS Code</a>
                                        </li>
                                    </Submenu>
                                </li>

                                <li className="submenu__item">
                                    <a href="https://docs.mongodb.com/guides/">Guides</a>
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
                            <a href="https://www.mongodb.com/download-center?jmp=docs">Get MongoDB</a>
                        </li>
                        <li className="menu__item menu__item--secondary">
                            <a href="https://www.mongodb.com/contact?jmp=docs">Contact Us</a>
                        </li>
                    </Menu>
                </div>
            </div>
        );
    }
}

export default NavbarDropdown;
