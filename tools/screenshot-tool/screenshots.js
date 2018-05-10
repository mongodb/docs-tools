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
  let loginInfo = {};

  if (argv[3] !== undefined) {
    const properties = PropertiesReader(argv[3]);
    loginInfo = {
      username: properties.get('user.login.username'),
      password: properties.get('user.login.password')
    }
  }

  const screenshotNames = await script.run({
    nightmare: nightmare,
    screenshot_dir: './screenshots-temp/',
    loginToAtlas: function() {
      nightmare.goto('https://cloud.mongodb.com/user#/atlas/login')
      nightmare.wait('input[name="username"]');

      if (loginInfo.username && loginInfo.password) {
        nightmare.type('input[name="username"]', loginInfo.username);
        nightmare.type('input[name="password"]', loginInfo.password);
      }
      else {
        throw new Error("No login information specified");
      }
      nightmare.click('.login-form-submit-button');
    }
  });

  // Compare the images
  for (const image of screenshotNames) {
    await util.compareImages(image);
  }

}

main(process.argv).catch((err) => console.error(err))
