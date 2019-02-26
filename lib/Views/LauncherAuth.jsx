import React from 'react';
import PropTypes from 'prop-types';

import MenuPanel from 'terriajs/lib/ReactViews/StandardUserInterface/customizable/MenuPanel.jsx';
import PanelStyles from 'terriajs/lib/ReactViews/Map/Panels/panel.scss';
import Styles from './related-maps.scss';
import classNames from 'classnames';

function getPersistentItem(key) {
    let value = localStorage.getItem(key);
    if (value) {
        return value;
    }
    return '';
}

class LauncherAuth extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            username: getPersistentItem('ewatercycle.launcher.username'),
            password: getPersistentItem('ewatercycle.launcher.password')
        }
        this.onUsernameChange = this.onUsernameChange.bind(this);
        this.onPasswordChange = this.onPasswordChange.bind(this);
        this.onSubmit = this.onSubmit.bind(this);
        this.logOut = this.logOut.bind(this);
    }

    onUsernameChange(e) {
        this.setState({ username: e.target.value });
    }

    onPasswordChange(e) {
        this.setState({ password: e.target.value });
    }

    onSubmit() {
        localStorage.setItem('ewatercycle.launcher.username', this.state.username);
        localStorage.setItem('ewatercycle.launcher.password', this.state.password);
        event.preventDefault();
        this.forceUpdate();
        // TODO check if credentials are OK
    }

    logOut() {
        localStorage.removeItem('ewatercycle.launcher.username');
        localStorage.removeItem('ewatercycle.launcher.password');
        this.setState({
            username: '',
            password: ''
        });
    }

    isAuthenticated() {
        return getPersistentItem('ewatercycle.launcher.username') && getPersistentItem('ewatercycle.launcher.password');
    }

    render() {
        const dropdownTheme = {
            inner: Styles.dropdownInner
        };
        // TODO add icon like https://octicons.github.com/icon/sign-in/

        if (this.isAuthenticated()) {
            return (
                <div className="tjs-panel__panel">
                    <button
                        onClick={this.logOut}
                        type='button'
                        className="tjs-panel__button tjs-_buttons__btn tjs-_buttons__btn--map"
                        title='Logout'
                    >
                        <span>Logout</span>
                    </button>
                </div>
            );
        }

        return (
            <MenuPanel theme={dropdownTheme}
                btnText="Login"
                smallScreen={this.props.smallScreen}
                viewState={this.props.viewState}
                btnTitle="Login to start experiments">
                <div className={classNames(PanelStyles.header)}>
                    <label className={PanelStyles.heading}>Login to start experiments</label>
                </div>
                <form>
                    <label>
                        Username
                    <input className="tjs-_form__field tjs-_form__input" type="text" value={this.state.username} onChange={this.onUsernameChange}></input>
                    </label>
                    <label>
                        Password
                    <input className="tjs-_form__field tjs-_form__input" type="password" value={this.state.password} onChange={this.onPasswordChange}></input>
                    </label>
                    <button className="tjs-_buttons__btn tjs-_buttons__btn-primary" type="submit" onClick={this.onSubmit}>Login</button>
                </form>
            </MenuPanel>
        );
    }
}

export default LauncherAuth;
