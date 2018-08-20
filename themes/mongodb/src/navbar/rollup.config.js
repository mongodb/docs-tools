import babel from 'rollup-plugin-babel';
import commonjs from 'rollup-plugin-commonjs';
import {eslint} from 'rollup-plugin-eslint';
import {minify} from 'uglify-es';
import replace from 'rollup-plugin-replace';
import resolve from 'rollup-plugin-node-resolve';
import {uglify} from 'rollup-plugin-uglify';

export default {
    'input': 'navbar/navbar.js',
    'plugins': [
        eslint({
            'include': 'navbar/**',
            'throwOnError': true
        }),
        replace({
          'process.env.NODE_ENV': JSON.stringify('production')
        }),
        resolve(),
        commonjs({'include': 'node_modules/**'}),
        babel({
            exclude: 'node_modules/**'
        }),
        uglify({}, minify)
    ],
    'output': {
        'format': 'iife'
    }
};

