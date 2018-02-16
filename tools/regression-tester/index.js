'use strict'

const assert = require('assert')
const process = require('process')
const Nightmare = require('nightmare')
const pixelmatch = require('pixelmatch')
require('nightmare-load-filter')(Nightmare)

Nightmare.action('getClipboard',
    function(name, options, parent, win, renderer, done) {
        const {clipboard} = require('electron')
        parent.respondTo('getClipboard', function(done) {
            const text = clipboard.readText()
            done(null, text)
        })

        done()
    }, function(done) {
        this.child.call('getClipboard', done)
    }
)

Nightmare.action('clearClipboard',
    function(name, options, parent, win, renderer, done) {
        const {clipboard} = require('electron')
        parent.respondTo('clearClipboard', function(done) {
            clipboard.writeText('')
            done()
        })

        done()
    }, function(done) {
        this.child.call('clearClipboard', done)
    }
)

Nightmare.action('getBBox', function(selector, done) {
    this.evaluate_now((selector) => {
        const element = document.querySelector(selector)
        if (!element) { return null }
        return {
            x: element.offsetLeft,
            y: element.offsetTop,
            width: element.offsetWidth,
            height: element.offsetHeight
        }
    }, done, selector)
})

Nightmare.action('isVisible', function(selector, done) {
    this.evaluate_now((selector) => {
        const element = document.querySelector(selector)
        if (!element) { return false }
        return element.offsetParent !== null
    }, done, selector)
})

Nightmare.action('screenshotWithSize',
    function(name, options, parent, win, renderer, done) {
        parent.respondTo('screenshotWithSize', function(clip, done) {
            const FrameManager = require('./frame-manager')
            const frameManager = FrameManager(win)

            const args = [function handleCapture (img) {
                const size = img.getSize()
                done(null, [img.toBitmap(), size.width, size.height])
            }]

            if (clip) {
                args.unshift(clip)
            }

            frameManager.requestFrame(function() {
                win.capturePage.apply(win, args)
            })
        })

        done()
    },
    function(clip, done) {
        this.child.call('screenshotWithSize', clip, done)
    }
)

const [BASE_PATH, TEST_PATH] = [process.env.BASE_PATH, process.env.TEST_PATH]
const EXPECTED_TEXT = `db.inventory.insertOne(
   { item: "canvas", qty: 100, tags: ["cotton"], size: { h: 28, w: 35.5, uom: "cm" } }
)`
const AD_URLS = ['https://securepubads.g.doubleclick.net/*']

function getBasePath(path) {
    return `${BASE_PATH}/${path}`
}

function getTestPath(path) {
    return `${TEST_PATH}/${path}`
}

class Comparison {
    constructor() {
        const options = {width: 1400, height: 1500}
        this.nightmareBase = Nightmare(options)
        this.nightmareTest = Nightmare(options)
    }

    get base() {
        return this.nightmareBase
    }

    get test() {
        return this.nightmareTest
    }

    goto(pageName) {
        return Promise.all([
            this.nightmareBase.filter({urls: AD_URLS}, function(details, cb) {
                cb({cancel: true})
            }).goto(getBasePath(pageName)),
            this.nightmareTest.filter({urls: AD_URLS}, function(details, cb) {
                cb({cancel: true})
            }).goto(getTestPath(pageName)),
        ])
    }

    call(methodName, ...args) {
        return Promise.all([
            this.nightmareBase[methodName](...args),
            this.nightmareTest[methodName](...args)
        ])
    }

    async compare(selector) {
        const [baseBBox, testBBox] = await Promise.all([
            this.nightmareBase.getBBox(selector),
            this.nightmareTest.getBBox(selector)
        ])

        const [baseShot, testShot] = await Promise.all([
            this.nightmareBase.screenshotWithSize(baseBBox),
            this.nightmareTest.screenshotWithSize(testBBox)
        ])

        const [width, height] = baseShot.slice(1)
        const differentPixels = pixelmatch(baseShot[0].data, testShot[0].data, null, width, height)
        assert.strictEqual(differentPixels, 0)
    }
}

const engine = new Comparison()

describe('widgets', function() {
    this.timeout('30s')
    this.slow('10s')

    describe('copy button', function() {
        it('should correctly copy code', async function() {
            await engine.base.clearClipboard()
            await engine.base.goto(getTestPath('insert-documents.html'))
            await engine.base.wait('.copy-button')
            await engine.base.click('.copy-button')
            const text = await engine.base.getClipboard()
            assert.strictEqual(text, EXPECTED_TEXT)
        })
    })

    describe('page', function() {
        it('should look the same', async function() {
            await engine.goto('insert-documents.html')
            await engine.compare('body')
        })
    })

    describe('tabs', function() {
        it('should go to the first tab if no preference is saved', async function() {
            assert(await engine.test.isVisible('.tabpanel-shell'), 'Shell should be shown')
            assert(!(await engine.test.isVisible('.tabpanel-compass')), 'Compass should not be shown')
        })

        it('should show only the correct tab\'s contents when choosing a new tab', async function() {
            await engine.call('click', '[data-tabid="compass"]')
            assert(!await engine.test.isVisible('.tabpanel-shell'), 'Shell should not be shown')
            assert((await engine.test.isVisible('.tabpanel-compass')), 'Compass should be shown')
        })

        it('should go to the previously-selected tab if a preference is saved', async function() {
            await engine.call('refresh')
            assert(!await engine.test.isVisible('.tabpanel-shell'), 'Shell should not be shown')
            assert((await engine.test.isVisible('.tabpanel-compass')), 'Compass should be shown')
        })

        it('should show a dropdown menu when the dropdown menu is clicked', async function() {
            await engine.call('click', '.tab-strip .dropdown-toggle')
            assert(await engine.test.isVisible('[data-tabid="php"]'), 'PHP button should be shown')
            await engine.compare('.tab-strip')
        })

        it('should show the correct tab\'s contents when an element in the dropdown menu is clicked', async function() {
            await engine.call('click', '[data-tabid="php"]')
            assert(!await engine.test.isVisible('.tabpanel-compass'), 'Compass should not be shown')
            assert((await engine.test.isVisible('.tabpanel-php')), 'PHP should be shown')
        })
    })

    describe('deluge', function() {
        it('should be closed by default', async function() {
            await engine.compare('.deluge')
            const [beforeHeight, afterHeight] = await engine.call('evaluate', () => {
                return document.querySelector('.deluge').offsetHeight
            })

            assert(afterHeight < 50, `too tall: ${afterHeight}px`)
        })

        it('should open when clicked', async function() {
            await engine.call('click', '.deluge-header')
            await engine.base.wait(500)
            await engine.compare('.deluge')
            const afterHeight = await engine.test.evaluate(() => {
                return document.querySelector('.deluge').offsetHeight
            })

            assert(afterHeight > 50, `too short: ${afterHeight}px`)
        })
    })

    after(async function() {
        await engine.call('end')
    })
})
