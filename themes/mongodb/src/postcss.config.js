module.exports = ctx => ({
  map: false,
  plugins: {
    'postcss-import': { root: ctx.file.dirname },
    'postcss-nested': { },
    'postcss-responsive-type': { },
    'postcss-cssnext': {
        browsers: "defaults, IE >= 10",
        warnings: true,
        preserve: false
    },
    'postcss-clean': {
        level: {
            2: {
                mergeSemantically: true,
                restructureRules: true
            }
        },
        skipRebase: true,
        inline: 'local,fonts.googleapis.com'
    }
  }
})
