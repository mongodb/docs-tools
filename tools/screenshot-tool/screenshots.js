'use strict';

var fs = require('fs-extra');
var Nightmare = require('nightmare');
var screenshotSelector = require('nightmare-screenshot-selector');
var path = require('path');
var PropertiesReader = require('properties-reader');
//var properties = PropertiesReader(__dirname + '/.properties.ini');
var util = require('./util.js');

Nightmare.action('screenshotSelector', screenshotSelector);

async function main(argv) {
  const script = require(argv[2]);
  const nightmare = Nightmare(script.nightmare_props);
  const screenshotNames = await script.run({
    nightmare: nightmare,
    screenshot_dir: './screenshots-temp/'
  });

  // Compare the images
  for (const image of screenshotNames) {
    await util.compareImages(image);
  }

}

main(process.argv).catch((err) => console.error(err))
