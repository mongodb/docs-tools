module.exports = ctx => ({
  map: false,
  plugins: {
    'postcss-import': { root: ctx.file.dirname },
    'postcss-responsive-type': { },

    // postcss-nested allows token concatenation, which is not included
    // in the nested rule spec. e.g. &__nested
    'postcss-nested': { },

    'postcss-preset-env': {
        stage: 2,
        browsers: "defaults, IE >= 10"
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
