var fs = require('fs-extra');
var Nightmare = require('nightmare');
var screenshotSelector = require('nightmare-screenshot-selector');
var path = require('path');
var util = require('./util.js');

Nightmare.action('screenshotSelector', screenshotSelector);

var filename = path.basename(__filename).slice(0, -3);

const orig_image_dir = './source/images/charts/';
const screenshot_dir = './screenshots-temp/charts/';
const screenshot_names = ['charts-dashboard.png'];

async function run() {
  console.log('Running ' + path.basename(__filename));

  // Start Nightmare
  var nightmare = Nightmare(util.charts_props);

  // Go to charts landing page
  await nightmare.goto('http://charts.mongodb.parts/dashboards/01674446-c816-43e9-9a01-5efff19d523e')
  await nightmare.wait('.react-grid-item')
  await nightmare.wait(1000)

  // Get the screen area with the top toolbar removed
  const dashboardRect = await nightmare.evaluate(() => {
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
  })

  // Convert to a clip object that nightmare can use and round down pixel values
  const dashboardClip = {
    x: Math.floor(dashboardRect.left),
    y: Math.floor(dashboardRect.top),
    width: Math.floor(dashboardRect.width),
    height: Math.floor(dashboardRect.height + 1000)
  };

  await nightmare.screenshot(screenshot_dir + screenshot_names[0])
  await nightmare.wait(500)
  await nightmare.end();

  // Compare the images
  for (const image of screenshot_names) {
    await util.compareImages(image);
  }
}

run().catch((err) => console.error(err))
