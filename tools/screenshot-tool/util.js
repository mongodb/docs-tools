const fs = require('fs-extra');
const readline = require('readline-sync');
const compareImages = require('resemblejs/compareImages');
const sharp = require('sharp');

async function getDiff(screenshot, orig_image) {
  const options = {
    output: {
        errorColor: {
            red: 255,
            green: 0,
            blue: 255
        },
        errorType: 'movement',
        transparency: 0.3,
        largeImageThreshold: 1200,
        useCrossOrigin: false,
        outputDiff: true
    },
    scaleToSameSize: true,
    ignore: ['nothing', 'less', 'antialiasing', 'colors', 'alpha'],
  };

  const data = await compareImages(screenshot, orig_image);

  console.log('Mismatch percentage for: ' + screenshot + ': ' + data.misMatchPercentage);

  if (data && data.misMatchPercentage > 3) {
    await fs.writeFile(screenshot.slice(0, -4) + '-diff.png', data.getBuffer());
    var answer = readline.question('Do you want to replace ' + screenshot + '? Check screenshots-temp to compare. (y / n)');
    if (answer == 'y') {
      console.log('Replacing image...\n');
      fs.copySync(screenshot, orig_image);
    }
  }
  else {
    console.log('Images are the same. No update needed.\n');
  }
}

/**
 * Resizes images larger than the docs content pane (750px) using Sharp.
 * IMPORTANT, READ BEFORE USING:
 * To avoid blurry images on various displays, currently the
 * preferred screenshot method is to configure
 * Nightmare to take screenshots at 1500px width and let Sphinx
 * resize using :scale: or :figwidth: as this looks best on
 * retina and non-retina displays.
 */
async function resizeImage(screenshot) {
  // Load the screenshot image into sharp.js
  const screenshotImg = sharp(screenshot);

  // Get the metadata and see if it's larger than page (750px)
  const metadata = await screenshotImg.metadata()
  console.log(metadata);
  if (metadata.width > 750) {

    // Sharp can't replace images so create a temp filename to store the resized image
    var screenshot_temp = screenshot.slice(0, screenshot.indexOf(".png")) + "-temp" + screenshot.slice(screenshot.indexOf(".png"));

    // Resize the image to what will fit on our page
    await screenshotImg.resize(721, null)
    await screenshotImg.toFile(screenshot_temp);
    await fs.rename(screenshot_temp, screenshot);
    return;
  }
}

var methods = {
  compareImages: async function(filename) {
    var orig_image = filename[0];
    var screenshot = filename[1];

    if (fs.existsSync(orig_image)) {
      getDiff(screenshot, orig_image);
    }
    else {
      fs.copySync(screenshot, orig_image);
      console.log('Moved screenshot');
    }
    return;
  }
}

module.exports = methods;
