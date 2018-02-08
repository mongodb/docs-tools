import buble from 'rollup-plugin-buble'
import { minify } from 'uglify-es'
import eslint from 'rollup-plugin-eslint'
import resolve from 'rollup-plugin-node-resolve'
import svelte from 'rollup-plugin-svelte'
import uglify from 'rollup-plugin-uglify'

export default {
    input: 'js/controller.js',
    plugins: [
        eslint({
            include: 'js/**',
            throwOnError: true,
        }),
        svelte(),
        resolve(),
        buble({
            transforms: {
                dangerousForOf: true
            }
        }),
        uglify({}, minify)
    ],
    output: {
        file: '../static/controller.js',
        format: 'iife'
    }
}

