import babel from 'rollup-plugin-babel';
import commonjs from 'rollup-plugin-commonjs';
import {eslint} from 'rollup-plugin-eslint';
import {minify} from 'uglify-es';
import resolve from 'rollup-plugin-node-resolve';
import {uglify} from 'rollup-plugin-uglify';

export default {
    'input': 'landing/landing.js',
    'plugins': [
        eslint({
            'include': 'landing/**',
            'throwOnError': true
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

