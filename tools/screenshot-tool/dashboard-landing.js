var fs = require('fs-extra');
var Nightmare = require('nightmare');
var screenshotSelector = require('nightmare-screenshot-selector');
var path = require('path');
var util = require('./util.js');

Nightmare.action('screenshotSelector', screenshotSelector);

var filename = path.basename(__filename).slice(0, -3);

const orig_image_dir = './source/images/charts/';
const screenshot_dir = './charts-screenshots-temp/';
const screenshot_names = ['charts-dashboard-landing.png'];

async function run() {
  console.log('Running ' + path.basename(__filename));

  // Start Nightmare
  var nightmare = Nightmare(util.nightmare_props);

  // Go to charts landing page
  await nightmare.goto(util.nightmare_props.url)
  await nightmare.wait('.Charts_dashboard-overview_list---QP2c0')
  await nightmare.wait(1000)

  // Get the screen area with the top toolbar removed
  const landingRect = await nightmare.evaluate(() => {
    var page_body = document.querySelector('#root');
    var [rect] = page_body.getClientRects();
    return {
      top: rect.top,
      right: rect.right,
      bottom: rect.bottom,
      left: rect.left,
      width: rect.width,
      height: rect.height
    };
  });

  // Convert to a clip object that nightmare can use and round down pixel values
  const landingClip = {
    x: Math.floor(landingRect.left),
    y: Math.floor(landingRect.top),
    width: Math.floor(landingRect.width),
    height: 650
  };

  await nightmare.screenshot(screenshot_dir + screenshot_names[0], landingClip)
  await nightmare.wait(500)
  await nightmare.end();

  // Compare the images
  for (const image of screenshot_names) {
    await util.compareImages(image);
  }
}

run().catch((err) => console.error(err))
