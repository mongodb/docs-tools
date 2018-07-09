'use strict';

const fs = require('fs-extra');
const Nightmare = require('nightmare');
const screenshotSelector = require('nightmare-screenshot-selector');
const path = require('path');
const PropertiesReader = require('properties-reader');
const util = require('./util.js');

Nightmare.action('screenshotSelector', screenshotSelector);

async function main(argv) {
  const script = require(argv[2]);
  const nightmare = Nightmare(script.nightmare_props);
  let atlasLoginInfo = {};
  let chartsLoginInfo = {};

  if (argv[3] !== undefined) {
    const properties = PropertiesReader(argv[3]);
    atlasLoginInfo = {
      username: properties.get('atlasUser.login.username'),
      password: properties.get('atlasUser.login.password')
    }
    chartsLoginInfo = {
      email: properties.get('chartsUser.login.email'),
      password: properties.get('chartsUser.login.password')
    }
  }

  const screenshotNames = await script.run({
    nightmare: nightmare,
    screenshot_dir: './screenshots-temp/',
    loginToAtlas: function() {
      nightmare.goto('https://cloud.mongodb.com/user#/atlas/login')
      nightmare.wait('input[name="username"]');

      if (atlasLoginInfo.username && atlasLoginInfo.password) {
        nightmare.type('input[name="username"]', atlasLoginInfo.username);
        nightmare.type('input[name="password"]', atlasLoginInfo.password);
      }
      else {
        throw new Error("No login information specified");
      }
      nightmare.click('.login-form-submit-button');
    },
    loginToCharts: function() {
      nightmare.goto('http://charts.mongodb.parts/login')
      nightmare.wait('input#email');

      if (chartsLoginInfo.email && chartsLoginInfo.password) {
        nightmare.type('input#email', chartsLoginInfo.email);
        nightmare.type('input#password', chartsLoginInfo.password);
      }
      else {
        throw new Error("No login information specified");
      }
      nightmare.click('[data-test-id="login-form-submit-button"]');
    }
  });

  // Compare the images
  for (const image of screenshotNames) {
    await util.compareImages(image);
  }

}

main(process.argv).catch((err) => console.error(err))
