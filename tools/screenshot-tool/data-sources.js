var fs = require('fs-extra');
var Nightmare = require('nightmare');
var screenshotSelector = require('nightmare-screenshot-selector');
var path = require('path');
var PropertiesReader = require('properties-reader');
var properties = PropertiesReader(__dirname + '/.properties.ini');
var util = require('./util.js');

Nightmare.action('screenshotSelector', screenshotSelector);

/* const login_user_selector = '.login-form-group-control[name=username]';
const login_pass_selector = '.login-form-group-control[name=password]';

const username = properties.get('user.login.username');
const password = properties.get('user.login.password'); */

var filename = path.basename(__filename).slice(0, -3);

const orig_image_dir = './source/images/charts/';
const screenshot_dir = './screenshots-temp/';
const screenshot_names = ['data-sources-view.png'];

async function run() {
  console.log('Running ' + path.basename(__filename));

  // Start Nightmare
  // TODO RENAME THIS!!!
  var nightmare = Nightmare(util.charts_props);

  // Go to atlas login page and login
  await nightmare.goto('http://charts.mongodb.parts')
  await nightmare.wait(10000)
  // await nightmare.wait('.Charts_app_root---1mxm7')

  /* await nightmare.wait(login_user_selector)
  await nightmare.type(login_user_selector, username)
  await nightmare.type(login_pass_selector, password) */
  await nightmare.click('#\\31')
  await nightmare.wait(1000)
  await nightmare.screenshot(screenshot_dir + screenshot_names[0])
  await nightmare.wait(2000)
  await nightmare.end();

  // Compare the images
  for (const image of screenshot_names) {
    await util.compareImages(image);
  }
}

run().catch((err) => console.error(err))
